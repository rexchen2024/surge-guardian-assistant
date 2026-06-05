#!/usr/bin/env python3
"""Surge realtime guardian.

Healthy/no-action output is {"wakeAgent": false}. Incident text is intended to
wake Hermes or another agent for analysis.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path


SURGE_CLI = os.environ.get("SURGE_CLI", "/Applications/Surge.app/Contents/Applications/surge-cli")
LOG_DIR = Path(os.path.expandvars(os.environ.get("SURGE_LOG_DIR", "${HOME}/Library/Logs/Surge"))).expanduser()
STATE_DIR = Path(os.path.expandvars(os.environ.get("STATE_DIR", "${HOME}/.hermes/state/surge-hermes-healthcheck"))).expanduser() / "realtime"
STATE_FILE = STATE_DIR / "state.json"
DOMAIN = os.environ.get("CHECK_DOMAIN", "")
IP = os.environ.get("CHECK_IP", "")
POLICIES = [item.strip() for item in os.environ.get("EXPECTED_POLICIES", "").split(",") if item.strip()]
PROXY_POLICY = os.environ.get("PROXY_POLICY", "Proxy")
DIRECT_FAIL_WINDOW_SECONDS = int(os.environ.get("DIRECT_FAIL_WINDOW_SECONDS", "900"))
TEMP_RULE_REVIEW_SECONDS = int(os.environ.get("TEMP_RULE_REVIEW_SECONDS", "43200"))

STATE_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], timeout: int = 20) -> dict[str, object]:
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "code": -1, "stdout": "", "stderr": str(exc)}


def load_state() -> dict[str, object]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state: dict[str, object]) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    tmp.replace(STATE_FILE)


def event_key(event: dict[str, object]) -> str:
    raw = "|".join(str(event.get(k, "")) for k in ("identifier", "date", "content", "type"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def latest_log_file() -> Path | None:
    files = sorted(LOG_DIR.glob("Surge-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_new_log_lines(state: dict[str, object]) -> tuple[list[str], Path | None]:
    path = latest_log_file()
    if not path:
        return [], None
    stat = path.stat()
    sig = f"{path}:{stat.st_ino}"
    prior = state.get("log", {})
    prior = prior if isinstance(prior, dict) else {}
    offset = 0 if prior.get("sig") != sig else int(prior.get("offset", 0) or 0)
    if offset > stat.st_size:
        offset = 0
    with path.open("r", errors="replace") as handle:
        handle.seek(offset)
        data = handle.read()
        new_offset = handle.tell()
    state["log"] = {"sig": sig, "offset": new_offset, "path": str(path)}
    return [line for line in data.splitlines() if line.strip()], path


def dump_events() -> tuple[list[dict[str, object]], dict[str, object]]:
    raw = run([SURGE_CLI, "--raw", "dump", "event"], timeout=10)
    if not raw["ok"] or not raw["stdout"]:
        return [], raw
    try:
        data = json.loads(str(raw["stdout"]))
        return data.get("events", []) or [], raw
    except Exception as exc:
        raw["ok"] = False
        raw["stderr"] = f"event json parse failed: {exc}"
        return [], raw


def is_ignored_log(line: str) -> bool:
    ignored = [
        "Unknown VIF virtual IP",
        "REJECT policy upgraded to REJECT-DROP",
        "Resource update completed:",
    ]
    if "Resource update completed:" in line and "error: N/A" not in line:
        return False
    return any(token in line for token in ignored)


def parse_direct_failure_host(line: str) -> str | None:
    match = re.search(r"Connection setup failed .*? to ([^,\s]+?)(?::(\d+))? via DIRECT", line)
    if not match:
        return None
    host = match.group(1).strip().lower().rstrip(".")
    if not host or re.fullmatch(r"\d+(?:\.\d+){3}", host):
        return None
    if ":" in host or host.endswith((".local", ".lan", ".home", ".cn")):
        return None
    return host


def classify_log(line: str) -> dict[str, object] | None:
    if is_ignored_log(line):
        return None
    if "<NETWORK-ERROR>" not in line and "<ERROR>" not in line and "<WARNING>" not in line:
        return None
    if "SGExternalResource" in line and "error: N/A" not in line:
        return {"kind": "external_resource", "severity": "medium", "line": line}
    if "Encrypted DNS error" in line or "DNS query timeout" in line:
        return {"kind": "dns", "severity": "low", "line": line}
    direct_host = parse_direct_failure_host(line)
    if direct_host:
        return {"kind": "direct_domain_failure", "severity": "low", "line": line, "host": direct_host}
    if any(policy in line for policy in POLICIES):
        return {"kind": "proxy", "severity": "high", "line": line}
    if "<ERROR>" in line:
        return {"kind": "surge_error", "severity": "medium", "line": line}
    return None


def classify_event(event: dict[str, object]) -> dict[str, object] | None:
    ident = str(event.get("identifier", ""))
    content = str(event.get("content", ""))
    etype = event.get("type")
    text = f"{ident} {content}"
    if "policy.fatal.error" in ident or "policy.too.many.error" in ident:
        return {"kind": "proxy", "severity": "high", "event": event}
    if etype == 2 and "error" in text.lower():
        return {"kind": "surge_event", "severity": "medium", "event": event}
    return None


def short_json(result: dict[str, object], limit: int = 500) -> str:
    text = str(result.get("stdout") or result.get("stderr") or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def test_policies() -> dict[str, dict[str, object]]:
    return {policy: run([SURGE_CLI, "--raw", "test-policy", policy], timeout=20) for policy in POLICIES}


def update_external_resources() -> dict[str, object]:
    return run([SURGE_CLI, "--raw", "external-resource", "update", "all"], timeout=60)


def add_temp_proxy_rule(host: str) -> tuple[str, dict[str, object]]:
    rule = f"DOMAIN,{host},{PROXY_POLICY}"
    return rule, run([SURGE_CLI, "--raw", "add-temp-rule", rule], timeout=10)


def remove_temp_proxy_rule(rule: str) -> dict[str, object]:
    return run([SURGE_CLI, "--raw", "del-temp-rule", rule], timeout=10)


def policy_test_ok(result: dict[str, object]) -> bool:
    text = f"{result.get('stdout') or ''} {result.get('stderr') or ''}"
    return bool(result.get("ok")) and '"error"' not in text and "error" not in text.lower()


def check_cert() -> dict[str, object]:
    if not IP or not DOMAIN:
        return {"ok": False, "code": -1, "stdout": "", "stderr": "CHECK_IP or CHECK_DOMAIN missing"}
    first = run(["openssl", "s_client", "-connect", f"{IP}:443", "-servername", DOMAIN], timeout=12)
    if not first["ok"] and not first["stdout"]:
        return first
    proc = subprocess.run(
        ["openssl", "x509", "-noout", "-subject", "-dates", "-ext", "subjectAltName"],
        input=str(first["stdout"]),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=12,
    )
    return {"ok": proc.returncode == 0, "code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def render_incident(incidents: list[dict[str, object]], actions: list[str], diagnostics: list[str], log_path: Path | None) -> str:
    lines = [
        "Surge 实时守护发现需要分析的异常",
        "",
        f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"日志：{log_path or 'N/A'}",
        "",
        "【异常摘要】",
    ]
    for item in incidents[:12]:
        if "event" in item:
            event = item["event"]
            event = event if isinstance(event, dict) else {}
            lines.append(f"- [{item['severity']}] {item['kind']}: {event.get('identifier')} | {event.get('content')} | {event.get('date')}")
        else:
            lines.append(f"- [{item['severity']}] {item['kind']}: {item.get('line')}")
    if len(incidents) > 12:
        lines.append(f"- 另外还有 {len(incidents) - 12} 条同类异常已折叠")
    if actions:
        lines.extend(["", "【已自动执行的低风险处理】"])
        lines.extend(f"- {action}" for action in actions)
    if diagnostics:
        lines.extend(["", "【现场诊断】"])
        lines.extend(f"- {item}" for item in diagnostics)
    lines.extend([
        "",
        "【AI 分析要求】",
        "- 判断这是临时波动、可自动修复问题，还是需要人工介入的问题。",
        "- 已自动处理的动作要说明效果；不能确认恢复就明确说不能确认。",
        "- 涉及改 Surge 配置、切换长期策略、重启 Surge、改服务器、改证书、改 DNS 记录时，只能给方案并请求确认。",
        "- 回复要短，优先给结论、原因、已处理、建议下一步。",
    ])
    return "\n".join(lines)


def should_alert_for_recovered_proxy(counters: dict[str, object]) -> bool:
    now = int(time.time())
    window_started = int(counters.get("proxy_transient_window_started", 0) or 0)
    if not window_started or now - window_started > 3600:
        counters["proxy_transient_window_started"] = now
        counters["proxy_transient_recovered"] = 1
        return False
    counters["proxy_transient_recovered"] = int(counters.get("proxy_transient_recovered", 0) or 0) + 1
    return int(counters["proxy_transient_recovered"]) >= 3


def update_direct_failure_state(state: dict[str, object], log_items: list[dict[str, object]], actions: list[str]) -> list[dict[str, object]]:
    now = int(time.time())
    failures = state.setdefault("direct_failures", {})
    temp_rules = state.setdefault("temp_proxy_rules", {})
    failures = failures if isinstance(failures, dict) else {}
    temp_rules = temp_rules if isinstance(temp_rules, dict) else {}
    active_hosts = {str(item["host"]) for item in log_items if item.get("kind") == "direct_domain_failure" and item.get("host")}

    for host, info in list(failures.items()):
        if now - int(info.get("last", 0) or 0) > DIRECT_FAIL_WINDOW_SECONDS:
            failures.pop(host, None)

    reviews = state.setdefault("temp_rule_reviews", [])
    reviews = reviews if isinstance(reviews, list) else []
    for host, info in list(temp_rules.items()):
        if host in active_hosts:
            continue
        added_at = int(info.get("added_at", 0) or 0)
        last_review = int(info.get("last_review", 0) or 0)
        if now - max(added_at, last_review) < TEMP_RULE_REVIEW_SECONDS:
            continue
        res_update = update_external_resources()
        res_remove = remove_temp_proxy_rule(str(info["rule"]))
        info["last_review"] = now
        reviews.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "host": host,
            "rule": info["rule"],
            "updated_resources": bool(res_update["ok"]),
            "removed": bool(res_remove["ok"]),
            "reason": "periodic temp-rule cleanup; cloud rules get first chance again",
        })
        if res_remove["ok"]:
            temp_rules.pop(host, None)
    state["temp_rule_reviews"] = reviews[-50:]

    escalated = []
    for host in active_hosts:
        info = failures.setdefault(host, {"count": 0, "first": now, "last": now})
        if now - int(info.get("first", now) or now) > DIRECT_FAIL_WINDOW_SECONDS:
            info.clear()
            info.update({"count": 0, "first": now, "last": now})
        info["count"] = int(info.get("count", 0) or 0) + 1
        info["last"] = now

        if info["count"] == 2 and now - int(info.get("last_acl_update", 0) or 0) > 1800:
            res = update_external_resources()
            info["last_acl_update"] = now
            actions.append(f"检测到 {host} 直连反复失败，已优先同步外部资源：{'成功' if res['ok'] else '失败'} {short_json(res)}")

        if info["count"] >= 3 and host not in temp_rules:
            rule, res = add_temp_proxy_rule(host)
            if res["ok"]:
                temp_rules[host] = {
                    "rule": rule,
                    "added_at": now,
                    "reason": "repeated DIRECT failures before cloud rules caught up",
                    "failure_count": info["count"],
                }
                actions.append(f"已为 {host} 添加运行时临时代理规则：{rule}")
                escalated.append({
                    "kind": "direct_domain_failure",
                    "severity": "medium",
                    "line": f"{host} 在 {DIRECT_FAIL_WINDOW_SECONDS // 60} 分钟内直连失败 {info['count']} 次，已临时走代理",
                    "host": host,
                })
            else:
                escalated.append({
                    "kind": "direct_domain_failure",
                    "severity": "medium",
                    "line": f"{host} 反复直连失败，但添加临时代理规则失败：{short_json(res)}",
                    "host": host,
                })
    return escalated


def main() -> None:
    if not POLICIES:
        print("Surge 实时守护配置缺失：EXPECTED_POLICIES 为空")
        return

    state = load_state()
    events, _event_raw = dump_events()
    log_lines, log_path = read_new_log_lines(state)

    seen = set(state.get("seen_events", []))
    current_keys = [event_key(event) for event in events]

    if not state.get("initialized"):
        state["initialized"] = True
        state["seen_events"] = current_keys[-200:]
        state.setdefault("counters", {})
        save_state(state)
        print('{"wakeAgent": false}')
        return

    incidents = []
    for event in events:
        key = event_key(event)
        if key in seen:
            continue
        item = classify_event(event)
        if item:
            incidents.append(item)
        seen.add(key)

    log_items = [item for line in log_lines for item in [classify_log(line)] if item]
    incidents.extend(log_items)

    counters = state.setdefault("counters", {})
    counters = counters if isinstance(counters, dict) else {}
    dns_new = sum(1 for item in log_items if item["kind"] == "dns")
    if dns_new:
        counters["dns"] = int(counters.get("dns", 0) or 0) + dns_new
    else:
        counters["dns"] = max(0, int(counters.get("dns", 0) or 0) - 1)

    actions: list[str] = []
    diagnostics: list[str] = []
    important = [item for item in incidents if item["severity"] in {"high", "medium"}]
    if int(counters["dns"]) >= 5:
        important.append({"kind": "dns", "severity": "medium", "line": f"DNS errors reached consecutive score {counters['dns']}"})
    important.extend(update_direct_failure_state(state, log_items, actions))

    if not important:
        state["seen_events"] = list(seen)[-200:]
        state["counters"] = counters
        save_state(state)
        print('{"wakeAgent": false}')
        return

    kinds = {str(item["kind"]) for item in important}

    if "dns" in kinds and int(counters["dns"]) >= 5:
        res = run([SURGE_CLI, "--raw", "flush", "dns"], timeout=10)
        actions.append(f"已刷新 Surge DNS 缓存：{'成功' if res['ok'] else '失败'} {short_json(res)}")
        counters["dns"] = 0

    if "external_resource" in kinds:
        res = update_external_resources()
        actions.append(f"已尝试更新全部外部资源：{'成功' if res['ok'] else '失败'} {short_json(res)}")

    if "proxy" in kinds:
        tests = test_policies()
        for policy, result in tests.items():
            diagnostics.append(f"{policy} 连通性测试：{'成功' if policy_test_ok(result) else '异常'} {short_json(result)}")
        cert = check_cert()
        diagnostics.append(f"{DOMAIN} 证书探测：{'成功' if cert['ok'] and f'DNS:{DOMAIN}' in str(cert.get('stdout', '')) else '异常'} {short_json(cert, 700)}")
        policies_ok = all(policy_test_ok(result) for result in tests.values())
        cert_ok = bool(cert["ok"]) and f"DNS:{DOMAIN}" in str(cert.get("stdout", ""))
        if kinds == {"proxy"} and policies_ok and cert_ok and not should_alert_for_recovered_proxy(counters):
            state["seen_events"] = list(seen)[-200:]
            state["counters"] = counters
            suppressed = state.setdefault("suppressed", [])
            suppressed = suppressed if isinstance(suppressed, list) else []
            suppressed.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "proxy event recovered during verification",
                "count_in_window": counters.get("proxy_transient_recovered", 0),
                "items": len(important),
            })
            state["suppressed"] = suppressed[-50:]
            save_state(state)
            print('{"wakeAgent": false}')
            return
        if not policies_ok:
            counters["proxy_transient_recovered"] = 0

    state["seen_events"] = list(seen)[-200:]
    state["counters"] = counters
    save_state(state)
    print(render_incident(important, actions, diagnostics, log_path))


if __name__ == "__main__":
    main()

