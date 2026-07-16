from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

from . import __version__
from .cdn_watch import (
    CdnWatchDaemon,
    ServiceTracker,
    ack_pending,
    ensure_daemon,
    load_watch_settings,
    pid_path,
    process_is_watcher,
    read_pid,
    resolve_pending,
    stop_daemon,
)
from .config import DEFAULT_SURGE_CLI, SentryConfig, write_env
from .sentry import SurgeSentry
from .redact import redact_text, scan
from .surge import SurgeClient, latest_surge_log
from .traffic import current_month_db, diff_records, latest_session_db, read_policy_records, records_to_snapshot, total_gb


DISPLAY_NAME = "Surge Sentry"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def discover_surge_cli() -> str:
    return shutil.which("surge-cli") or DEFAULT_SURGE_CLI


def discover_profiles() -> list[Path]:
    candidates = [
        Path.home() / "Library/Mobile Documents/iCloud~com~nssurge~inc/Documents",
        Path.home() / "Library/Application Support/Surge/Profiles",
    ]
    profiles: list[Path] = []
    for base in candidates:
        if base.exists():
            profiles.extend(sorted(base.rglob("*.conf")))
    return profiles


def choose_profile(label: str, profiles: list[Path]) -> str:
    if not profiles:
        return prompt(label)
    print(f"\n{label} candidates:")
    for idx, path in enumerate(profiles[:12], 1):
        print(f"  {idx}. {path}")
    raw = prompt(f"{label} number or path", "1")
    if raw.isdigit() and 1 <= int(raw) <= min(len(profiles), 12):
        return str(profiles[int(raw) - 1])
    return raw


def discover_policies(surge_cli: str) -> list[str]:
    client = SurgeClient(surge_cli)
    policy, _ = client.dump_policy()
    proxies = policy.get("proxies", [])
    if isinstance(proxies, list):
        return [str(item) for item in proxies]
    return []


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def command_version(_args: argparse.Namespace) -> int:
    print(f"{DISPLAY_NAME} {__version__}")
    return 0


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def write_json_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    tmp.chmod(0o600)
    tmp.replace(path)
    path.chmod(0o600)


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def slugify(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    text = "-".join(part for part in text.split("-") if part)
    return text[:48] or "default"


def build_hermes_cron_command(root: Path) -> list[str]:
    script = root / "scripts" / "surge-sentry"
    prompt_path = root / "hermes" / "job-prompts" / "sentry.md"
    return [
        "hermes",
        "cron",
        "create",
        "*/1 * * * *",
        prompt_path.read_text(),
        "--name",
        DISPLAY_NAME,
        "--script",
        str(script),
        "--workdir",
        str(root),
    ]


def auto_update_if_due(config: SentryConfig) -> None:
    if not config.auto_update:
        return
    root = config.root
    if not (root / ".git").exists():
        return

    state_path = config.state_dir / "update-state.json"
    state = read_json(state_path)
    now = int(time.time())
    last = int(state.get("last_check_at", 0) or 0)
    if now - last < config.auto_update_interval_seconds:
        return

    state["last_check_at"] = now
    try:
        status = run_git(root, "status", "--porcelain", "--untracked-files=no")
        if status.returncode != 0:
            state["last_result"] = "git status failed"
            return
        if status.stdout.strip():
            state["last_result"] = "skipped: local tracked files changed"
            return

        fetch = run_git(root, "fetch", "--prune", "origin")
        if fetch.returncode != 0:
            state["last_result"] = "git fetch failed"
            return

        upstream = run_git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        upstream_ref = upstream.stdout.strip() if upstream.returncode == 0 else "origin/main"
        counts = run_git(root, "rev-list", "--left-right", "--count", f"HEAD...{upstream_ref}")
        if counts.returncode != 0:
            state["last_result"] = f"cannot compare with {upstream_ref}"
            return
        ahead, behind = [int(item) for item in counts.stdout.split()]
        if behind == 0:
            state["last_result"] = "up to date"
            return
        if ahead:
            state["last_result"] = "skipped: local branch has unpublished commits"
            return

        pull = run_git(root, "pull", "--ff-only")
        if pull.returncode != 0:
            state["last_result"] = "git pull failed"
            return

        check = subprocess.run(
            ["scripts/check"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        state["last_result"] = "updated" if check.returncode == 0 else "updated but check failed"
    except Exception as exc:
        state["last_result"] = f"failed: {exc}"
    finally:
        state["last_finished_at"] = int(time.time())
        write_json_private(state_path, state)


def command_setup(args: argparse.Namespace) -> int:
    root = project_root()
    env_path = root / ".env"
    print(f"{DISPLAY_NAME} setup")
    print("This writes local .env only. It will not be committed.\n")

    surge_cli = prompt("surge-cli path", discover_surge_cli())
    log_dir = prompt("Surge log directory", str(Path.home() / "Library/Logs/Surge"))
    profiles = discover_profiles()
    mac_profile = choose_profile("Primary Surge profile", profiles)
    mobile_profile = prompt("Optional secondary/mobile profile", "")

    policies = discover_policies(surge_cli)
    if policies:
        print("\nRuntime policy candidates:")
        for item in policies[:24]:
            print(f"  - {item}")
    expected = prompt("Expected policy names, comma-separated", ",".join(policies[:2]) if len(policies) >= 2 else "")
    proxy_policy = prompt("Policy/group used for temporary proxy rules", "Proxy")
    check_domain = prompt("Optional health-check domain", "")
    check_ip = prompt("Optional health-check IP", "")

    values = {
        "SURGE_CLI": surge_cli,
        "SURGE_LOG_DIR": log_dir,
        "MAC_PROFILE": mac_profile,
        "EXPECTED_POLICIES": expected,
        "PROXY_POLICY": proxy_policy,
        "STATE_DIR": "${HOME}/.hermes/state/surge-sentry",
        "DIRECT_FAIL_WINDOW_SECONDS": "900",
        "TEMP_RULE_REVIEW_SECONDS": "43200",
        "EXTERNAL_RESOURCE_FAIL_THRESHOLD": "2",
        "DNS_FAIL_THRESHOLD": "10",
        "DIRECT_FAIL_THRESHOLD": "3",
        "POLICY_RECOVERED_ALERT_THRESHOLD": "3",
        "ALERT_COOLDOWN_SECONDS": "3600",
        "AUTO_UPDATE": "1",
        "AUTO_UPDATE_INTERVAL_SECONDS": "86400",
        "CDN_WATCH_ENABLED": "0",
        "CDN_WATCH_CONFIG": str(root / "config" / "cdn-watch.local.json"),
    }
    if mobile_profile:
        values["MOBILE_PROFILE"] = mobile_profile
    if check_domain:
        values["CHECK_DOMAIN"] = check_domain
    if check_ip:
        values["CHECK_IP"] = check_ip
    write_env(env_path, values)
    print(f"\nWrote {env_path}")

    if args.print_hermes_command or args.install_hermes:
        cmd = build_hermes_cron_command(root)
        print("\nHermes cron command:")
        print(" ".join(shlex.quote(item) for item in cmd))
        if args.install_hermes:
            result = subprocess.run(cmd, text=True)
            return result.returncode
    return 0


def command_tick(_args: argparse.Namespace) -> int:
    config = SentryConfig.load(project_root())
    auto_update_if_due(config)
    if config.cdn_watch_enabled:
        ok, detail = ensure_daemon(config)
        if not ok:
            print(f"Surge Sentry CDN Watch 启动失败：{detail}")
    print(SurgeSentry(config).tick())
    return 0


def command_cdn_watch(args: argparse.Namespace) -> int:
    config = SentryConfig.load(project_root())
    if args.cdn_watch_command == "ensure":
        ok, detail = ensure_daemon(config)
        if not args.quiet:
            print(f"cdn-watch: {detail}")
        return 0 if ok else 1
    if args.cdn_watch_command == "stop":
        ok, detail = stop_daemon(config)
        print(f"cdn-watch: {detail}")
        return 0 if ok else 1
    if args.cdn_watch_command == "status":
        state = read_json(config.state_dir / "cdn-watch-state.json")
        pid = read_pid(config)
        allowed = {
            "phase", "status", "updated_at", "last_mbps", "cdn", "host",
            "watch_state", "last_request_at", "controller_at", "controller_latency_ms", "event_errors",
        }
        services = {
            str(name): {key: value for key, value in info.items() if key in allowed}
            for name, info in (state.get("services", {}) or {}).items()
            if isinstance(info, dict)
        }
        summary = {
            "enabled": config.cdn_watch_enabled,
            "running": process_is_watcher(pid),
            "pid": pid if process_is_watcher(pid) else 0,
            "heartbeat": state.get("daemon_heartbeat"),
            "services": services,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.cdn_watch_command == "ack":
        ok, detail = ack_pending(config, args.event_id)
        print(f"cdn-watch: {detail}")
        return 0 if ok else 1
    if not config.cdn_watch_config.exists():
        print(f"cdn-watch: config missing: {config.cdn_watch_config}")
        return 1
    try:
        settings = load_watch_settings(config.cdn_watch_config)
    except Exception as exc:
        print(f"cdn-watch: invalid config: {exc}")
        return 1
    if args.cdn_watch_command == "resolve":
        if args.file != "-":
            print("cdn-watch: resolve currently accepts --file - only")
            return 1
        ok, detail = resolve_pending(
            config,
            args.event_id,
            sys.stdin.read(),
            target=settings.notify_target,
        )
        print(f"cdn-watch: {detail}")
        return 0 if ok else 1
    if args.cdn_watch_command == "once":
        client = SurgeClient(config.surge_cli)
        data, result = client.dump_requests()
        if not result.get("ok"):
            print("cdn-watch: Surge request data unavailable")
            return 1
        now = time.time()
        trackers = [ServiceTracker(spec) for spec in settings.services]
        matched = 0
        rows = []
        for key in ("active-requests", "recent-requests"):
            rows.extend(data.get(key, []) if isinstance(data, dict) else [])
        seen: set[str] = set()
        for event in rows:
            key = str(event.get("id"))
            if key in seen:
                continue
            seen.add(key)
            for tracker in trackers:
                if tracker.ingest(event, now):
                    matched += 1
                    break
        output = {
            "matched_requests": matched,
            "services": [tracker.evaluate(now).__dict__ for tracker in trackers],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    current = read_pid(config)
    if current and current != os.getpid() and process_is_watcher(current):
        print(f"cdn-watch: already running (pid {current})")
        return 0
    path = pid_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(os.getpid()) + "\n")
    path.chmod(0o600)
    try:
        return CdnWatchDaemon(config, settings).run(stop_after_seconds=max(0, args.seconds))
    finally:
        if read_pid(config) == os.getpid():
            path.unlink(missing_ok=True)


def traffic_db_for_scope(config: SentryConfig, scope: str) -> Path | None:
    if scope == "session":
        return latest_session_db(config.traffic_stat_dir)
    return current_month_db(config.traffic_stat_dir) or latest_session_db(config.traffic_stat_dir)


def traffic_monitor_path(config: SentryConfig, name: str) -> Path:
    return config.state_dir / "traffic-monitors" / f"{slugify(name)}.json"


def traffic_patterns(config: SentryConfig, raw: str) -> list[str]:
    patterns = split_csv(raw) if raw else list(config.traffic_policy_patterns)
    return patterns or ["%"]


def read_traffic_snapshot(config: SentryConfig, scope: str, patterns: list[str], limit: int) -> tuple[Path | None, list]:
    db_path = traffic_db_for_scope(config, scope)
    if not db_path:
        return None, []
    return db_path, read_policy_records(db_path, patterns, limit=limit)


def format_monitor_report(state: dict, records: list, *, status: str, top: int) -> str:
    baseline = state.get("baseline", {}) if isinstance(state.get("baseline"), dict) else {}
    deltas = diff_records(records, baseline)
    total = total_gb(deltas)
    started_at = state.get("started_at", "unknown")
    name = state.get("name", "default")
    scope = state.get("scope", "month")
    lines = [
        f"Surge Sentry 流量监控：{name}",
        f"状态：{status}",
        f"开始：{started_at}",
        f"范围：{scope}",
        f"本阶段消耗：{total:.2f}GB",
    ]
    note = state.get("note")
    if note:
        lines.append(f"备注：{note}")
    if deltas:
        by_policy: dict[str, float] = {}
        for item in deltas:
            by_policy[item.policy or "(unknown)"] = by_policy.get(item.policy or "(unknown)", 0.0) + item.total_gb
        lines.extend(["", "按策略汇总："])
        for policy, value in sorted(by_policy.items(), key=lambda item: item[1], reverse=True)[:top]:
            lines.append(f"- {policy}: {value:.2f}GB")
        lines.extend(["", "Top 消耗："])
        for item in deltas[:top]:
            host = item.host or item.path or "(unknown)"
            lines.append(
                f"- {host}: {item.total_gb:.2f}GB "
                f"(down {item.down_gb:.2f}GB / up {item.up_gb:.2f}GB, {item.requests} requests, {item.policy or 'unknown'})"
            )
    else:
        lines.extend(["", "暂无新增流量。"])
    return "\n".join(lines)


def command_traffic(args: argparse.Namespace) -> int:
    config = SentryConfig.load(project_root())
    patterns = traffic_patterns(config, args.policy_patterns)
    monitor_path = traffic_monitor_path(config, args.name)

    if args.traffic_command == "start":
        db_path, records = read_traffic_snapshot(config, args.scope, patterns, args.limit)
        if not db_path:
            print("traffic: 未找到 Surge 流量统计库")
            return 1
        state = {
            "name": args.name,
            "scope": args.scope,
            "policy_patterns": patterns,
            "db_path": str(db_path),
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": args.note or "",
            "baseline": records_to_snapshot(records),
        }
        write_json_private(monitor_path, state)
        print(f"已开始流量监控：{args.name}")
        print(f"基线库：{db_path.name}")
        print(f"基线流量：{total_gb(records):.2f}GB")
        print("后续运行 `scripts/surge-sentry traffic status` 查看进行中结果，结束时运行 `scripts/surge-sentry traffic end`。")
        return 0

    state = read_json(monitor_path)
    if not state:
        print(f"traffic: 未找到监控任务 {args.name}，请先运行 start")
        return 1

    scope = str(state.get("scope") or args.scope)
    patterns = list(state.get("policy_patterns") or patterns)
    db_path, records = read_traffic_snapshot(config, scope, patterns, args.limit)
    if not db_path:
        print("traffic: 未找到 Surge 流量统计库")
        return 1

    status = "进行中" if args.traffic_command == "status" else "已结束"
    print(format_monitor_report(state, records, status=status, top=args.top))
    if args.traffic_command == "end":
        state["ended_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        state["final_db_path"] = str(db_path)
        state["final_total_gb"] = total_gb(diff_records(records, state.get("baseline", {})))
        archive = monitor_path.with_suffix(f".ended-{int(time.time())}.json")
        write_json_private(archive, state)
        monitor_path.unlink(missing_ok=True)
        print(f"\n记录已归档：{archive}")
    return 0


def command_doctor(_args: argparse.Namespace) -> int:
    config = SentryConfig.load(project_root())
    client = SurgeClient(config.surge_cli)
    print(f"{DISPLAY_NAME} doctor")
    print("")
    print(f"Config: {'present' if config.env_path.exists() else 'missing .env'}")
    print(f"surge-cli: {config.surge_cli} ({'ok' if os.path.exists(config.surge_cli) else 'not found'})")
    print(f"log dir: {config.surge_log_dir} ({'ok' if config.surge_log_dir.exists() else 'missing'})")
    latest = latest_surge_log(config.surge_log_dir)
    print(f"latest log: {latest.name if latest else 'none'}")
    print(f"expected policies: {', '.join(config.expected_policies) if config.expected_policies else 'missing'}")

    env, env_result = client.dump_environment()
    runtime_env = env.get("environment", env) if isinstance(env, dict) else {}
    print(f"environment: {'ok' if env_result['ok'] and runtime_env else 'unavailable'}")
    if runtime_env:
        safe_keys = ["ProxyMode", "MitMEnabled", "RewriteEnabled", "ScriptingEnabled", "Replica"]
        safe = {key: runtime_env.get(key) for key in safe_keys if key in runtime_env}
        print(f"runtime flags: {json.dumps(safe, ensure_ascii=False)}")

    policy, policy_result = client.dump_policy()
    print(f"policy dump: {'ok' if policy_result['ok'] and policy else 'unavailable'}")
    proxies = policy.get("proxies", []) if isinstance(policy, dict) else []
    if proxies:
        print(f"proxy count: {len(proxies)}")

    for label, path in [("primary profile", config.mac_profile), ("secondary profile", config.mobile_profile)]:
        if not path:
            continue
        result = client.check_profile(path)
        print(f"{label}: {'ok' if result['ok'] else 'failed'}")
    return 0


def command_redact_check(_args: argparse.Namespace) -> int:
    root = project_root()
    findings = scan(root)
    if not findings:
        print("redact-check: ok")
        return 0
    print("redact-check: possible private content found")
    for item in findings:
        print(f"- {item.path}:{item.line} [{item.kind}] {item.text}")
    return 1


def yesno(value: bool) -> str:
    return "yes" if value else "no"


def build_feedback_report(config: SentryConfig, include_check: bool = False) -> str:
    client = SurgeClient(config.surge_cli)
    latest = latest_surge_log(config.surge_log_dir)
    update_state = read_json(config.state_dir / "update-state.json")

    lines = [
        f"# {DISPLAY_NAME} Feedback Report",
        "",
        "Review this before sharing. Remove anything you do not want to send.",
        "",
        f"version: {__version__}",
        f"platform: {platform.system()} {platform.release()}",
        f"python: {platform.python_version()}",
        f"git_checkout: {yesno((config.root / '.git').exists())}",
        f"config_present: {yesno(config.env_path.exists())}",
        f"surge_cli_found: {yesno(os.path.exists(config.surge_cli))}",
        f"log_dir_found: {yesno(config.surge_log_dir.exists())}",
        f"latest_surge_log_found: {yesno(bool(latest))}",
        f"primary_profile_configured: {yesno(bool(config.mac_profile))}",
        f"secondary_profile_configured: {yesno(bool(config.mobile_profile))}",
        f"auto_update: {yesno(config.auto_update)}",
        f"auto_update_interval_seconds: {config.auto_update_interval_seconds}",
        f"last_update_result: {update_state.get('last_result', 'none')}",
    ]

    env, env_result = client.dump_environment()
    runtime_env = env.get("environment", env) if isinstance(env, dict) else {}
    lines.append(f"surge_environment_available: {yesno(bool(env_result['ok'] and runtime_env))}")

    policy, policy_result = client.dump_policy()
    proxies = policy.get("proxies", []) if isinstance(policy, dict) else []
    lines.append(f"surge_policy_available: {yesno(bool(policy_result['ok'] and policy))}")
    lines.append(f"surge_proxy_count: {len(proxies) if isinstance(proxies, list) else 0}")

    for label, path in [("primary_profile_check", config.mac_profile), ("secondary_profile_check", config.mobile_profile)]:
        if not path:
            lines.append(f"{label}: not configured")
            continue
        result = client.check_profile(path)
        lines.append(f"{label}: {'ok' if result['ok'] else 'failed'}")

    if include_check:
        check = subprocess.run(
            ["scripts/check"],
            cwd=config.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
        lines.extend([
            "",
            "## scripts/check",
            f"exit_code: {check.returncode}",
            "output:",
            check.stdout.strip()[-4000:] or "(empty)",
        ])

    return redact_text("\n".join(lines).strip() + "\n")


def command_feedback(args: argparse.Namespace) -> int:
    config = SentryConfig.load(project_root())
    report = build_feedback_report(config, include_check=args.with_check)

    if args.print:
        print(report, end="")
        return 0

    output = Path(args.output) if args.output else config.state_dir / "feedback-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report)
    output.chmod(0o600)
    print(f"feedback report: {output}")
    print("Review it before sharing. Nothing was uploaded.")

    if args.github_url:
        query = urlencode({
            "title": f"Feedback: {DISPLAY_NAME} issue",
            "body": report,
        })
        print(f"github issue url: https://github.com/rexchen2024/surge-guardian-assistant/issues/new?{query}")
    return 0


def command_update(args: argparse.Namespace) -> int:
    root = project_root()
    if not (root / ".git").exists():
        print("update: this install is not a git checkout; reinstall from GitHub to receive updates")
        return 1

    status = run_git(root, "status", "--porcelain", "--untracked-files=no")
    if status.returncode != 0:
        print(f"update: git status failed: {status.stderr.strip()}")
        return status.returncode
    if status.stdout.strip() and not args.force and not args.check:
        print("update: local tracked files have changes; commit/stash them first or rerun with --force")
        return 1

    fetch = run_git(root, "fetch", "--prune", "origin")
    if fetch.returncode != 0:
        print(f"update: git fetch failed: {fetch.stderr.strip()}")
        return fetch.returncode

    upstream = run_git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream_ref = upstream.stdout.strip() if upstream.returncode == 0 else "origin/main"
    counts = run_git(root, "rev-list", "--left-right", "--count", f"HEAD...{upstream_ref}")
    if counts.returncode != 0:
        print(f"update: cannot compare with {upstream_ref}: {counts.stderr.strip()}")
        return counts.returncode
    ahead, behind = [int(item) for item in counts.stdout.split()]

    if behind == 0:
        print(f"{DISPLAY_NAME} {__version__} is up to date")
        return 0
    if args.check:
        if ahead:
            print(f"updates available: {behind} commit(s) behind {upstream_ref}; local branch is also {ahead} commit(s) ahead")
        else:
            print(f"updates available: {behind} commit(s) behind {upstream_ref}")
        return 0
    if ahead and not args.force:
        print(f"update: local branch is {ahead} commit(s) ahead and {behind} behind; resolve manually")
        return 1

    pull = run_git(root, "pull", "--ff-only")
    if pull.returncode != 0:
        print(f"update: git pull failed: {pull.stderr.strip()}")
        return pull.returncode

    check = subprocess.run(["scripts/check"], cwd=root, text=True)
    if check.returncode != 0:
        print("update: code updated, but scripts/check failed; inspect the output above")
        return check.returncode
    print("update: complete")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="surge-sentry")
    parser.add_argument("--version", action="version", version=f"{DISPLAY_NAME} {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    version = sub.add_parser("version", help="print installed version")
    version.set_defaults(func=command_version)

    setup = sub.add_parser("setup", help="interactive first-run setup")
    setup.add_argument("--print-hermes-command", action="store_true", help="print a Hermes cron create command")
    setup.add_argument("--install-hermes", action="store_true", help="create the Hermes cron job after writing .env")
    setup.set_defaults(func=command_setup)

    tick = sub.add_parser("tick", help="one sentry run")
    tick.set_defaults(func=command_tick)

    traffic = sub.add_parser("traffic", help="start, inspect, or end a focused traffic monitor")
    traffic_sub = traffic.add_subparsers(dest="traffic_command", required=True)

    traffic_start = traffic_sub.add_parser("start", help="start a focused traffic monitor from the current Surge traffic baseline")
    traffic_start.add_argument("name", nargs="?", default="default", help="monitor name, for example f1-race or world-cup-fox")
    traffic_start.add_argument("--scope", choices=["session", "month"], default="month", help="Surge traffic database scope to compare")
    traffic_start.add_argument("--policy-patterns", default="", help="comma-separated SQL LIKE policy patterns; defaults to configured patterns or all policies")
    traffic_start.add_argument("--note", default="", help="short local note for this monitor")
    traffic_start.add_argument("--limit", type=int, default=500, help="maximum rows to read from Surge traffic stats")
    traffic_start.set_defaults(func=command_traffic)

    traffic_status = traffic_sub.add_parser("status", help="show traffic consumed since monitor start")
    traffic_status.add_argument("name", nargs="?", default="default", help="monitor name")
    traffic_status.add_argument("--scope", choices=["session", "month"], default="month", help="fallback scope if monitor state has no scope")
    traffic_status.add_argument("--policy-patterns", default="", help="fallback policy patterns if monitor state has none")
    traffic_status.add_argument("--limit", type=int, default=500, help="maximum rows to read from Surge traffic stats")
    traffic_status.add_argument("--top", type=int, default=8, help="number of top rows to display")
    traffic_status.set_defaults(func=command_traffic)

    traffic_end = traffic_sub.add_parser("end", help="finish a focused traffic monitor and archive the result")
    traffic_end.add_argument("name", nargs="?", default="default", help="monitor name")
    traffic_end.add_argument("--scope", choices=["session", "month"], default="month", help="fallback scope if monitor state has no scope")
    traffic_end.add_argument("--policy-patterns", default="", help="fallback policy patterns if monitor state has none")
    traffic_end.add_argument("--limit", type=int, default=500, help="maximum rows to read from Surge traffic stats")
    traffic_end.add_argument("--top", type=int, default=8, help="number of top rows to display")
    traffic_end.set_defaults(func=command_traffic)

    cdn_watch = sub.add_parser("cdn-watch", help="monitor real media request throughput and CDN health")
    cdn_watch_sub = cdn_watch.add_subparsers(dest="cdn_watch_command", required=True)

    cdn_ensure = cdn_watch_sub.add_parser("ensure", help="start the low-overhead watcher if needed")
    cdn_ensure.add_argument("--quiet", action="store_true", help="print nothing when healthy")
    cdn_ensure.set_defaults(func=command_cdn_watch)

    cdn_run = cdn_watch_sub.add_parser("run", help="run the persistent watcher in the foreground")
    cdn_run.add_argument("--seconds", type=float, default=0, help="optional test duration; zero runs continuously")
    cdn_run.set_defaults(func=command_cdn_watch)

    cdn_once = cdn_watch_sub.add_parser("once", help="inspect current matching media requests without changing Surge")
    cdn_once.set_defaults(func=command_cdn_watch)

    cdn_status = cdn_watch_sub.add_parser("status", help="show sanitized watcher state")
    cdn_status.set_defaults(func=command_cdn_watch)

    cdn_ack = cdn_watch_sub.add_parser("ack", help="archive a Hermes-processed pending media event")
    cdn_ack.add_argument("event_id", help="event id shown in the Sentry incident")
    cdn_ack.set_defaults(func=command_cdn_watch)

    cdn_resolve = cdn_watch_sub.add_parser("resolve", help="deliver a handled event and ack only after successful send")
    cdn_resolve.add_argument("event_id", help="event id shown in the Sentry incident")
    cdn_resolve.add_argument("--file", default="-", help="read the message from stdin; only '-' is accepted")
    cdn_resolve.set_defaults(func=command_cdn_watch)

    cdn_stop = cdn_watch_sub.add_parser("stop", help="stop the persistent watcher")
    cdn_stop.set_defaults(func=command_cdn_watch)

    doctor = sub.add_parser("doctor", help="manual sanitized diagnostic summary")
    doctor.set_defaults(func=command_doctor)

    redact = sub.add_parser("redact-check", help="scan repository for private content before commit")
    redact.set_defaults(func=command_redact_check)

    update = sub.add_parser("update", help="fetch and apply GitHub updates")
    update.add_argument("--check", action="store_true", help="only report whether updates are available")
    update.add_argument("--force", action="store_true", help="allow update despite local tracked changes or ahead commits")
    update.set_defaults(func=command_update)

    feedback = sub.add_parser("feedback", help="create a sanitized user feedback report")
    feedback.add_argument("--print", action="store_true", help="print the report instead of writing a file")
    feedback.add_argument("--output", help="write the report to this path")
    feedback.add_argument("--with-check", action="store_true", help="include scripts/check output")
    feedback.add_argument("--github-url", action="store_true", help="print a prefilled GitHub issue URL")
    feedback.set_defaults(func=command_feedback)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
