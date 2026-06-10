from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from . import __version__
from .config import DEFAULT_SURGE_CLI, GuardianConfig, write_env
from .guardian import SurgeGuardian
from .redact import scan
from .surge import SurgeClient, latest_surge_log


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
    print(f"Surge Guardian Assistant {__version__}")
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


def auto_update_if_due(config: GuardianConfig) -> None:
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
    print("Surge Guardian Assistant setup")
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
        "STATE_DIR": "${HOME}/.hermes/state/surge-guardian-assistant",
        "DIRECT_FAIL_WINDOW_SECONDS": "900",
        "TEMP_RULE_REVIEW_SECONDS": "43200",
        "EXTERNAL_RESOURCE_FAIL_THRESHOLD": "2",
        "DNS_FAIL_THRESHOLD": "10",
        "DIRECT_FAIL_THRESHOLD": "3",
        "POLICY_RECOVERED_ALERT_THRESHOLD": "3",
        "ALERT_COOLDOWN_SECONDS": "3600",
        "AUTO_UPDATE": "1",
        "AUTO_UPDATE_INTERVAL_SECONDS": "86400",
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
        script = root / "scripts" / "surge-guardian-assistant"
        prompt_path = root / "hermes" / "job-prompts" / "guardian.md"
        cmd = [
            "hermes",
            "cron",
            "create",
            "*/1 * * * *",
            prompt_path.read_text(),
            "--name",
            "Surge Guardian Assistant",
            "--script",
            str(script),
            "--workdir",
            str(root),
            "--skills",
            "Surge",
        ]
        print("\nHermes cron command:")
        print(" ".join(shlex.quote(item) for item in cmd))
        if args.install_hermes:
            result = subprocess.run(cmd, text=True)
            return result.returncode
    return 0


def command_tick(_args: argparse.Namespace) -> int:
    config = GuardianConfig.load(project_root())
    auto_update_if_due(config)
    print(SurgeGuardian(config).tick())
    return 0


def command_doctor(_args: argparse.Namespace) -> int:
    config = GuardianConfig.load(project_root())
    client = SurgeClient(config.surge_cli)
    print("Surge Guardian Assistant doctor")
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
        print(f"Surge Guardian Assistant {__version__} is up to date")
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
    parser = argparse.ArgumentParser(prog="surge-guardian-assistant")
    parser.add_argument("--version", action="version", version=f"Surge Guardian Assistant {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    version = sub.add_parser("version", help="print installed version")
    version.set_defaults(func=command_version)

    setup = sub.add_parser("setup", help="interactive first-run setup")
    setup.add_argument("--print-hermes-command", action="store_true", help="print a Hermes cron create command")
    setup.add_argument("--install-hermes", action="store_true", help="create the Hermes cron job after writing .env")
    setup.set_defaults(func=command_setup)

    tick = sub.add_parser("tick", help="one guardian run")
    tick.set_defaults(func=command_tick)

    doctor = sub.add_parser("doctor", help="manual sanitized diagnostic summary")
    doctor.set_defaults(func=command_doctor)

    redact = sub.add_parser("redact-check", help="scan repository for private content before commit")
    redact.set_defaults(func=command_redact_check)

    update = sub.add_parser("update", help="fetch and apply GitHub updates")
    update.add_argument("--check", action="store_true", help="only report whether updates are available")
    update.add_argument("--force", action="store_true", help="allow update despite local tracked changes or ahead commits")
    update.set_defaults(func=command_update)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
