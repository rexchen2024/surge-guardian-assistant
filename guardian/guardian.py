from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import GuardianConfig
from .state import StateStore
from .surge import SurgeClient, latest_surge_log


CAUTIOUS_DIRECT_EXACT_HOSTS = {
    "dns.alidns.com",
    "doh.pub",
}
CAUTIOUS_DIRECT_SUFFIXES = (
    ".alidns.com",
    ".aliyuncs.com",
    ".apple.com",
    ".icloud.com",
    ".meituan.net",
    ".mi.com",
    ".qq.com",
    ".163.com",
)


def short_text(result: dict[str, Any], limit: int = 420) -> str:
    text = str(result.get("stdout") or result.get("stderr") or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def event_key(event: dict[str, Any]) -> str:
    raw = "|".join(str(event.get(k, "")) for k in ("identifier", "date", "content", "type"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


@dataclass
class Incident:
    kind: str
    severity: str
    message: str
    host: str = ""


class SurgeGuardian:
    def __init__(self, config: GuardianConfig):
        self.config = config
        self.client = SurgeClient(config.surge_cli)
        self.store = StateStore(config.state_dir / "guardian-state.json")

    def read_new_log_lines(self, state: dict[str, Any]) -> tuple[list[str], Path | None]:
        path = latest_surge_log(self.config.surge_log_dir)
        if not path:
            return [], None
        stat = path.stat()
        sig = f"{path}:{stat.st_ino}"
        prior = state.get("log", {}) if isinstance(state.get("log"), dict) else {}
        offset = 0 if prior.get("sig") != sig else int(prior.get("offset", 0) or 0)
        if offset > stat.st_size:
            offset = 0
        with path.open("r", errors="replace") as handle:
            handle.seek(offset)
            data = handle.read()
            new_offset = handle.tell()
        state["log"] = {"sig": sig, "offset": new_offset, "path": str(path)}
        return [line for line in data.splitlines() if line.strip()], path

    def classify_log(self, line: str) -> Incident | None:
        if "Resource update completed:" in line and "error: N/A" in line:
            return None
        if "Resource update completed:" in line and "error:" in line:
            return Incident("external_resource", "medium", line)
        ignored = [
            "Unknown VIF virtual IP",
            "REJECT policy upgraded to REJECT-DROP",
            "Resource update completed:",
        ]
        if any(token in line for token in ignored):
            return None
        if "<NETWORK-ERROR>" not in line and "<ERROR>" not in line and "<WARNING>" not in line:
            return None
        if "SGExternalResource" in line:
            return Incident("external_resource", "medium", line)
        if "Encrypted DNS error" in line or "DNS query timeout" in line:
            return Incident("dns", "low", line)
        host = self.parse_direct_failure_host(line)
        if host:
            return Incident("direct_domain_failure", "low", line, host=host)
        if any(policy in line for policy in self.config.expected_policies):
            return Incident("proxy", "high", line)
        if "<ERROR>" in line:
            return Incident("surge_error", "medium", line)
        return None

    @staticmethod
    def parse_direct_failure_host(line: str) -> str:
        match = re.search(r"Connection setup failed .*? to ([^,\s]+?)(?::(\d+))? via DIRECT", line)
        if not match:
            return ""
        host = match.group(1).strip().lower().rstrip(".")
        if not host or re.fullmatch(r"\d+(?:\.\d+){3}", host):
            return ""
        if ":" in host or host.endswith((".local", ".lan", ".home", ".cn")):
            return ""
        return host

    @staticmethod
    def should_skip_temp_proxy(host: str) -> bool:
        return host in CAUTIOUS_DIRECT_EXACT_HOSTS or host.endswith(CAUTIOUS_DIRECT_SUFFIXES)

    @staticmethod
    def classify_event(event: dict[str, Any]) -> Incident | None:
        ident = str(event.get("identifier", ""))
        content = str(event.get("content", ""))
        etype = event.get("type")
        text = f"{ident} {content}"
        if "policy.fatal.error" in ident or "policy.too.many.error" in ident:
            return Incident("proxy", "high", f"{ident} | {content} | {event.get('date')}")
        if etype == 2 and "error" in text.lower():
            return Incident("surge_event", "medium", f"{ident} | {content} | {event.get('date')}")
        return None

    def policy_test_ok(self, result: dict[str, Any]) -> bool:
        text = f"{result.get('stdout') or ''} {result.get('stderr') or ''}"
        return bool(result.get("ok")) and '"error"' not in text and "error" not in text.lower()

    def update_external_resource_state(self, state: dict[str, Any], incidents: list[Incident], actions: list[str], important: list[Incident]) -> None:
        if not any(item.kind == "external_resource" for item in incidents):
            return
        counters = state.setdefault("counters", {})
        count = int(counters.get("external_resource", 0) or 0) + 1
        counters["external_resource"] = count
        result = self.client.external_resource_update_all()
        actions.append(f"已尝试更新全部外部资源：{'成功' if result['ok'] else '失败'} {short_text(result)}")
        if result["ok"]:
            counters["external_resource"] = 0
            state.setdefault("suppressed", []).append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "external resource recovered after retry",
            })
            return
        if count >= self.config.external_resource_fail_threshold:
            important.append(Incident("external_resource", "medium", f"外部资源更新连续失败 {count} 次，自动重试仍失败"))

    def update_dns_state(self, state: dict[str, Any], incidents: list[Incident], actions: list[str], important: list[Incident]) -> None:
        counters = state.setdefault("counters", {})
        dns_new = sum(1 for item in incidents if item.kind == "dns")
        if dns_new:
            counters["dns"] = int(counters.get("dns", 0) or 0) + dns_new
        else:
            counters["dns"] = max(0, int(counters.get("dns", 0) or 0) - 1)
        if int(counters["dns"]) >= self.config.dns_fail_threshold:
            result = self.client.flush_dns()
            actions.append(f"已刷新 Surge DNS 缓存：{'成功' if result['ok'] else '失败'} {short_text(result)}")
            now = int(time.time())
            last_flush = int(counters.get("last_dns_flush_at", 0) or 0)
            if now - last_flush > 1800:
                counters["dns_flush_repeats"] = 0
            counters["dns_flush_repeats"] = int(counters.get("dns_flush_repeats", 0) or 0) + 1
            counters["last_dns_flush_at"] = now
            if not result["ok"] or int(counters["dns_flush_repeats"]) >= 2:
                important.append(Incident("dns", "medium", f"DNS errors reached consecutive score {counters['dns']}"))
            else:
                state.setdefault("suppressed", []).append({
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": "dns errors handled by one successful flush",
                    "score": counters["dns"],
                })
            counters["dns"] = 0

    @staticmethod
    def rule_present(rule: str, rules_dump: dict[str, Any]) -> bool:
        if not rules_dump:
            return True
        return rule in json.dumps(rules_dump, ensure_ascii=False)

    def reconcile_temp_rules(self, state: dict[str, Any]) -> None:
        temp_rules = state.setdefault("temp_rules", {})
        legacy_temp_rules = state.get("temp_proxy_rules")
        if isinstance(legacy_temp_rules, dict):
            for host, info in legacy_temp_rules.items():
                temp_rules.setdefault(host, info)
            state.pop("temp_proxy_rules", None)
        if not temp_rules:
            return
        rules_dump, result = self.client.dump_rules()
        if not result.get("ok") or not rules_dump:
            return
        reviews = state.setdefault("temp_rule_reviews", [])
        for host, info in list(temp_rules.items()):
            rule = str(info.get("rule", ""))
            if not rule or self.rule_present(rule, rules_dump):
                continue
            reviews.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "host": host,
                "rule": rule,
                "updated_resources": False,
                "removed": True,
                "reason": "state reconciliation; rule is no longer present in Surge runtime",
            })
            temp_rules.pop(host, None)
        state["temp_rule_reviews"] = reviews[-50:]

    def update_direct_failure_state(self, state: dict[str, Any], incidents: list[Incident], actions: list[str]) -> list[Incident]:
        now = int(time.time())
        failures = state.setdefault("direct_failures", {})
        temp_rules = state.setdefault("temp_rules", {})
        legacy_temp_rules = state.get("temp_proxy_rules")
        if isinstance(legacy_temp_rules, dict):
            for host, info in legacy_temp_rules.items():
                temp_rules.setdefault(host, info)
            state.pop("temp_proxy_rules", None)
        escalated: list[Incident] = []
        active_hosts = {item.host for item in incidents if item.kind == "direct_domain_failure" and item.host}
        self.reconcile_temp_rules(state)

        for host, info in list(failures.items()):
            if now - int(info.get("last", 0) or 0) > self.config.direct_fail_window_seconds:
                failures.pop(host, None)

        for host, info in list(temp_rules.items()):
            if host in active_hosts:
                continue
            added_at = int(info.get("added_at", 0) or 0)
            last_review = int(info.get("last_review", 0) or 0)
            if now - max(added_at, last_review) < self.config.temp_rule_review_seconds:
                continue
            resource = self.client.external_resource_update_all()
            remove = self.client.del_temp_rule(str(info["rule"]))
            info["last_review"] = now
            state.setdefault("temp_rule_reviews", []).append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "host": host,
                "rule": info["rule"],
                "updated_resources": bool(resource["ok"]),
                "removed": bool(remove["ok"]),
                "reason": "periodic temp-rule cleanup; cloud rules get first chance again",
            })
            if remove["ok"]:
                temp_rules.pop(host, None)

        for host in active_hosts:
            info = failures.setdefault(host, {"count": 0, "first": now, "last": now})
            if now - int(info.get("first", now) or now) > self.config.direct_fail_window_seconds:
                info.clear()
                info.update({"count": 0, "first": now, "last": now})
            info["count"] = int(info.get("count", 0) or 0) + 1
            info["last"] = now

            if self.should_skip_temp_proxy(host):
                if info["count"] >= self.config.direct_fail_threshold:
                    state.setdefault("suppressed", []).append({
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "direct failure on cautious infrastructure host; no temp proxy rule added",
                        "host": host,
                        "count": info["count"],
                    })
                continue

            if info["count"] == 2 and now - int(info.get("last_resource_update", 0) or 0) > 1800:
                result = self.client.external_resource_update_all()
                info["last_resource_update"] = now
                actions.append(f"检测到 {host} 直连反复失败，已优先同步外部资源：{'成功' if result['ok'] else '失败'} {short_text(result)}")

            if info["count"] >= self.config.direct_fail_threshold and host not in temp_rules:
                rule = f"DOMAIN,{host},{self.config.proxy_policy}"
                result = self.client.add_temp_rule(rule)
                if result["ok"]:
                    temp_rules[host] = {
                        "rule": rule,
                        "added_at": now,
                        "reason": "repeated DIRECT failures before cloud rules caught up",
                        "failure_count": info["count"],
                    }
                    actions.append(f"已为 {host} 添加运行时临时代理规则：{rule}")
                    escalated.append(Incident("direct_domain_failure", "medium", f"{host} 在短时间内直连失败 {info['count']} 次，已临时走代理", host=host))
                else:
                    escalated.append(Incident("direct_domain_failure", "medium", f"{host} 反复直连失败，但添加临时代理规则失败：{short_text(result)}", host=host))
        return escalated

    def verify_proxy_incidents(self, state: dict[str, Any], important: list[Incident], diagnostics: list[str]) -> bool:
        if not any(item.kind == "proxy" for item in important):
            return False
        tests = {policy: self.client.test_policy(policy) for policy in self.config.expected_policies}
        for policy, result in tests.items():
            diagnostics.append(f"{policy} 连通性复测：{'成功' if self.policy_test_ok(result) else '异常'} {short_text(result)}")
        policies_ok = all(self.policy_test_ok(result) for result in tests.values())
        counters = state.setdefault("counters", {})
        if policies_ok:
            started = int(counters.get("proxy_recovered_window_started", 0) or 0)
            now = int(time.time())
            if not started or now - started > 3600:
                counters["proxy_recovered_window_started"] = now
                counters["proxy_recovered_count"] = 1
                return True
            counters["proxy_recovered_count"] = int(counters.get("proxy_recovered_count", 0) or 0) + 1
            return int(counters["proxy_recovered_count"]) < self.config.policy_recovered_alert_threshold
        counters["proxy_recovered_count"] = 0
        return False

    def apply_alert_cooldown(self, state: dict[str, Any], incidents: list[Incident]) -> list[Incident]:
        now = int(time.time())
        cooldowns = state.setdefault("alert_cooldowns", {})
        kept: list[Incident] = []
        for item in incidents:
            key = f"{item.kind}:{item.host or item.message[:120]}"
            prior = int(cooldowns.get(key, 0) or 0)
            if prior and now - prior < self.config.alert_cooldown_seconds:
                state.setdefault("suppressed", []).append({
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": "alert cooldown",
                    "key": key,
                })
                continue
            cooldowns[key] = now
            kept.append(item)
        state["suppressed"] = state.get("suppressed", [])[-50:]
        return kept

    def tick(self) -> str:
        missing = self.config.missing_required()
        if missing:
            return "Surge Hermes Guardian 配置缺失：" + ", ".join(missing)

        state = self.store.load()
        events, _event_raw = self.client.dump_events()
        lines, log_path = self.read_new_log_lines(state)
        current_event_keys = [event_key(event) for event in events]

        if not state.get("initialized"):
            state["initialized"] = True
            state["seen_events"] = current_event_keys[-200:]
            self.store.save(state)
            return '{"wakeAgent": false}'

        seen = set(state.get("seen_events", []))
        incidents: list[Incident] = []
        for event in events:
            key = event_key(event)
            if key in seen:
                continue
            item = self.classify_event(event)
            if item:
                incidents.append(item)
            seen.add(key)
        incidents.extend(item for line in lines for item in [self.classify_log(line)] if item)

        actions: list[str] = []
        diagnostics: list[str] = []
        important = [
            item for item in incidents
            if item.severity in {"high", "medium"} and item.kind != "external_resource"
        ]
        self.update_external_resource_state(state, incidents, actions, important)
        self.update_dns_state(state, incidents, actions, important)
        important.extend(self.update_direct_failure_state(state, incidents, actions))

        suppress_proxy = self.verify_proxy_incidents(state, important, diagnostics)
        if suppress_proxy and {item.kind for item in important} == {"proxy"}:
            state["seen_events"] = list(seen)[-200:]
            state.setdefault("suppressed", []).append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "reason": "proxy recovered during verification"})
            self.store.save(state)
            return '{"wakeAgent": false}'

        important = self.apply_alert_cooldown(state, important)

        if not important:
            state["seen_events"] = list(seen)[-200:]
            self.store.save(state)
            return '{"wakeAgent": false}'

        state["seen_events"] = list(seen)[-200:]
        self.store.save(state)
        return self.render_incident(important, actions, diagnostics, log_path)

    def render_incident(self, incidents: list[Incident], actions: list[str], diagnostics: list[str], log_path: Path | None) -> str:
        lines = [
            "Surge Hermes Guardian 发现需要分析的异常",
            "",
            f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"日志：{log_path.name if log_path else 'N/A'}",
            "",
            "【异常摘要】",
        ]
        for item in incidents[:12]:
            lines.append(f"- [{item.severity}] {item.kind}: {item.message}")
        if len(incidents) > 12:
            lines.append(f"- 另外还有 {len(incidents) - 12} 条同类异常已折叠")
        if actions:
            lines.extend(["", "【已自动执行的低风险处理】"])
            lines.extend(f"- {item}" for item in actions)
        if diagnostics:
            lines.extend(["", "【现场诊断】"])
            lines.extend(f"- {item}" for item in diagnostics)
        lines.extend([
            "",
            "【AI 分析要求】",
            "- 判断这是临时波动、已自动修复的问题，还是需要用户决策的问题。",
            "- 如果无需通知用户，最终回复必须只包含 [SILENT] 六个字符，不能附加解释、代码块或大小写变体。",
            "- 永久修改 profile、重启 Surge、修改证书/DNS/服务器时，只能给方案并请求确认。",
            "- 回复要短：结论、原因、已处理、下一步、可沉淀规则。",
        ])
        return "\n".join(lines)
