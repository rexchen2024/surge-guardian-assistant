from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import SentryConfig
from .contracts import audit_profile, load_contracts
from .cdn_watch import consume_pending, is_direct_policy
from .state import StateStore
from .surge import SurgeClient, latest_surge_log
from .traffic import analyze_traffic, current_month_db, find_direct_leak_records, format_top_records, latest_session_db, read_policy_records


CAUTIOUS_DIRECT_EXACT_HOSTS = {
    "dns.alidns.com",
    "doh.pub",
}
CAUTIOUS_DIRECT_SUFFIXES = (
    ".alidns.com",
    ".aliyuncs.com",
    ".apple.com",
    ".apple-cloudkit.com",
    ".icloud.com",
    ".meituan.net",
    ".mi.com",
    ".microsoft.com",
    ".qq.com",
    ".163.com",
)
RECURRING_NOISE_KINDS = {"dns", "direct_domain_failure", "proxy"}


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
    bypass_cooldown: bool = False


class SurgeSentry:
    def __init__(self, config: SentryConfig):
        self.config = config
        self.client = SurgeClient(config.surge_cli)
        self.store = StateStore(config.state_dir / "sentry-state.json")

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
    def is_direct_ip_failure(line: str) -> bool:
        return bool(
            re.search(
                r"Connection setup failed .*? to \d{1,3}(?:\.\d{1,3}){3}(?::\d+)? via DIRECT",
                line,
            )
        )

    @staticmethod
    def should_skip_temp_proxy(host: str) -> bool:
        return host in CAUTIOUS_DIRECT_EXACT_HOSTS or host.endswith(CAUTIOUS_DIRECT_SUFFIXES)

    @staticmethod
    def in_maintenance_window(window: dict[str, Any], local_time: time.struct_time | None = None) -> bool:
        current = local_time or time.localtime()
        minute = current.tm_hour * 60 + current.tm_min
        start = int(window.get("start_minute", 0) or 0)
        end = int(window.get("end_minute", 0) or 0)
        if start <= end:
            in_range = start <= minute < end
        else:
            in_range = minute >= start or minute < end
        return current.tm_wday == int(window.get("weekday", -1)) and in_range

    @staticmethod
    def remember_suppressed(state: dict[str, Any], entry: dict[str, Any], cooldown_seconds: int = 900) -> None:
        now = int(time.time())
        key = str(entry.get("suppress_key") or f"{entry.get('reason', '')}:{entry.get('host', '')}")
        cooldowns = state.setdefault("suppressed_cooldowns", {})
        info = cooldowns.setdefault(key, {"count": 0, "first": now, "last": 0})
        if now - int(info.get("first", now) or now) > 86400:
            info.clear()
            info.update({"count": 0, "first": now, "last": 0})
        info["count"] = int(info.get("count", 0) or 0) + 1
        info["last"] = now

        suppressed = state.setdefault("suppressed", [])
        if suppressed and now - int(info.get("last_appended", 0) or 0) < cooldown_seconds:
            for item in reversed(suppressed):
                if item.get("suppress_key") == key:
                    item.update(entry)
                    item["suppress_key"] = key
                    item["count"] = info["count"]
                    item["last_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    return

        item = dict(entry)
        item["suppress_key"] = key
        item["count"] = info["count"]
        suppressed.append(item)
        info["last_appended"] = now

    def record_background_noise(self, state: dict[str, Any], lines: list[str]) -> None:
        counts: dict[str, int] = {}
        for line in lines:
            if "Unknown VIF virtual IP" in line:
                counts["unknown_vif_virtual_ip"] = counts.get("unknown_vif_virtual_ip", 0) + 1
            elif self.is_direct_ip_failure(line):
                counts["direct_ip_connection_failure"] = counts.get("direct_ip_connection_failure", 0) + 1
        if not counts:
            return
        day = time.strftime("%Y-%m-%d")
        noise = state.setdefault("background_noise", {})
        if noise.get("day") != day:
            noise.clear()
            noise["day"] = day
            noise["counts"] = {}
        stored = noise.setdefault("counts", {})
        for key, count in counts.items():
            stored[key] = int(stored.get(key, 0) or 0) + count
        noise["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    def suppress_configured_maintenance_noise(self, state: dict[str, Any], incidents: list[Incident]) -> list[Incident]:
        if not self.config.maintenance_windows or not incidents:
            return incidents
        kept: list[Incident] = []
        for item in incidents:
            suppressed = False
            for window in self.config.maintenance_windows:
                kinds = set(window.get("kinds") or [])
                if item.kind in kinds and self.in_maintenance_window(window):
                    self.remember_suppressed(state, {
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "configured recurring maintenance window; transient Surge noise suppressed",
                        "kind": item.kind,
                        "host": item.host,
                        "suppress_key": f"configured maintenance:{window.get('weekday')}:{window.get('start_minute')}:{item.kind}:{item.host}",
                    })
                    suppressed = True
                    break
            if not suppressed:
                kept.append(item)
        return kept

    def record_recurring_noise_candidates(
        self,
        state: dict[str, Any],
        incidents: list[Incident],
        local_time: time.struct_time | None = None,
    ) -> list[Incident]:
        candidates: list[Incident] = []
        relevant = [item for item in incidents if item.kind in RECURRING_NOISE_KINDS]
        if not relevant:
            return candidates

        now = int(time.time())
        current = local_time or time.localtime(now)
        bucket_size = max(1, int(self.config.recurring_noise_bucket_minutes or 10))
        bucket = (current.tm_hour * 60 + current.tm_min) // bucket_size * bucket_size
        today = time.strftime("%Y-%m-%d", current)
        cutoff = now - int(self.config.recurring_noise_history_days or 35) * 86400
        patterns = state.setdefault("recurring_noise_patterns", {})

        for item in relevant:
            host_key = item.host or "_"
            key = f"{current.tm_wday}:{bucket}:{item.kind}:{host_key}"
            pattern = patterns.setdefault(key, {
                "weekday": current.tm_wday,
                "bucket_minute": bucket,
                "kind": item.kind,
                "host": item.host,
                "dates": [],
                "first": now,
                "last": 0,
                "last_reported": 0,
            })
            dates = [entry for entry in pattern.get("dates", []) if int(entry.get("ts", 0) or 0) >= cutoff]
            if not any(entry.get("date") == today for entry in dates):
                dates.append({"date": today, "ts": now})
            pattern["dates"] = dates[-12:]
            pattern["last"] = now

            enough = len(pattern["dates"]) >= max(2, int(self.config.recurring_noise_min_occurrences or 3))
            report_cooldown_ok = now - int(pattern.get("last_reported", 0) or 0) > 7 * 86400
            if enough and report_cooldown_ok:
                pattern["last_reported"] = now
                hour, minute = divmod(bucket, 60)
                host_text = f"，主机 {item.host}" if item.host else ""
                candidates.append(Incident(
                    "recurring_noise_pattern",
                    "medium",
                    f"{item.kind}{host_text} 已在相同星期/时间窗口附近出现 {len(pattern['dates'])} 次；这可能是路由器、上游网络或固定维护窗口导致。建议先确认是否存在定时重启/维护；确认后可在 MAINTENANCE_WINDOWS 中配置静默窗口。",
                ))
                self.remember_suppressed(state, {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": "recurring noise pattern detected",
                    "kind": item.kind,
                    "host": item.host,
                    "weekday": current.tm_wday,
                    "time_bucket": f"{hour:02d}:{minute:02d}",
                    "occurrences": len(pattern["dates"]),
                    "suppress_key": f"recurring pattern:{key}",
                })

        state["recurring_noise_patterns"] = {
            key: value
            for key, value in patterns.items()
            if int(value.get("last", 0) or 0) >= cutoff
        }
        return candidates

    @staticmethod
    def trim_state_lists(state: dict[str, Any]) -> None:
        if isinstance(state.get("suppressed"), list):
            state["suppressed"] = state["suppressed"][-50:]
        if isinstance(state.get("temp_rule_reviews"), list):
            state["temp_rule_reviews"] = state["temp_rule_reviews"][-50:]
        if isinstance(state.get("suppressed_cooldowns"), dict):
            now = int(time.time())
            state["suppressed_cooldowns"] = {
                key: value
                for key, value in state["suppressed_cooldowns"].items()
                if now - int(value.get("last", 0) or 0) < 86400
            }

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
            self.remember_suppressed(state, {
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
                self.remember_suppressed(state, {
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
        legacy_temp_rules = state.get("temp_sentry_rules")
        if isinstance(legacy_temp_rules, dict):
            for host, info in legacy_temp_rules.items():
                temp_rules.setdefault(host, info)
            state.pop("temp_sentry_rules", None)
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
        legacy_temp_rules = state.get("temp_sentry_rules")
        if isinstance(legacy_temp_rules, dict):
            for host, info in legacy_temp_rules.items():
                temp_rules.setdefault(host, info)
            state.pop("temp_sentry_rules", None)
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
                    self.remember_suppressed(state, {
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

    def analyze_traffic_usage(self, diagnostics: list[str]) -> list[Incident]:
        if not self.config.traffic_analysis_enabled:
            return []
        if not self.config.traffic_policy_patterns or self.config.traffic_monthly_cap_gb <= 0:
            diagnostics.append("流量分析已开启，但缺少 TRAFFIC_POLICY_PATTERNS 或 TRAFFIC_MONTHLY_CAP_GB")
            return []

        # ── 检查 Emby 策略组的当前运行时选择 ──
        emby_on_proxy = False
        emby_policy = ""
        env_data, _env_result = self.client.dump_environment()
        if isinstance(env_data, dict):
            proxy_selection = env_data.get("environment", {}).get("ProxyGroupSelection", {})
            emby_policy = proxy_selection.get("Emby", "")
            if emby_policy and not is_direct_policy(emby_policy):
                emby_on_proxy = True

        session_db = latest_session_db(self.config.traffic_stat_dir)
        month_db = current_month_db(self.config.traffic_stat_dir)
        if not session_db:
            diagnostics.append("流量分析未找到 Surge Session 统计库")
            return []

        session_records = read_policy_records(session_db, self.config.traffic_policy_patterns)
        monthly_records = read_policy_records(month_db, self.config.traffic_policy_patterns) if month_db else []

        if emby_on_proxy:
            # Emby 正在走代理 → 必须提醒，绕过冷却
            # 查当天和月度的 Emby 直连优先域名走代理的记录
            direct_leaks = find_direct_leak_records(
                session_records,
                self.config.traffic_direct_host_patterns,
                self.config.traffic_direct_leak_min_gb,
            )
            if not direct_leaks and monthly_records:
                direct_leaks = find_direct_leak_records(
                    monthly_records,
                    self.config.traffic_direct_host_patterns,
                    max(self.config.traffic_direct_leak_min_gb * 3, 5.0),
                )
            if direct_leaks:
                top = format_top_records(direct_leaks)
                total_gb = sum(r.total_gb for r in direct_leaks)
                incidents: list[Incident] = []
                incidents.append(Incident(
                    "traffic", "high",
                    f"Emby 当前走代理（{emby_policy}）消耗 {total_gb:.1f}GB。Top: {top}",
                    host="emby-on-proxy",
                    bypass_cooldown=True,
                ))
                return incidents

            # 策略选择本身不是事故；没有真实大流量就保持静默。
            return []

        # Emby 当前是 DIRECT → 只查当天有无漏走代理，不查历史月份
        risks = analyze_traffic(
            session_records,
            [],  # 不传月度数据，避免历史月份永久报警
            monthly_cap_gb=self.config.traffic_monthly_cap_gb,
            reset_day=self.config.traffic_reset_day,
            daily_warn_ratio=self.config.traffic_daily_warn_ratio,
            daily_critical_ratio=self.config.traffic_daily_critical_ratio,
            direct_host_patterns=self.config.traffic_direct_host_patterns,
            direct_leak_min_gb=self.config.traffic_direct_leak_min_gb,
        )
        incidents: list[Incident] = []
        for risk in risks:
            top = format_top_records(risk.top_records)
            message = risk.message if not top else f"{risk.message} Top: {top}"
            host = "direct-preferred-media" if "直连优先" in risk.message else "daily-budget"
            incidents.append(Incident("traffic", risk.severity, message, host=host))
        return incidents

    def apply_alert_cooldown(self, state: dict[str, Any], incidents: list[Incident]) -> list[Incident]:
        now = int(time.time())
        cooldowns = state.setdefault("alert_cooldowns", {})
        kept: list[Incident] = []
        for item in incidents:
            if item.bypass_cooldown:
                # 标记为 bypass_cooldown 的事件不受冷却限制
                kept.append(item)
                continue
            key = f"{item.kind}:{item.host or item.message[:120]}"
            prior = int(cooldowns.get(key, 0) or 0)
            if prior and now - prior < self.config.alert_cooldown_seconds:
                self.remember_suppressed(state, {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": "alert cooldown",
                    "key": key,
                    "suppress_key": f"alert cooldown:{key}",
                })
                continue
            cooldowns[key] = now
            kept.append(item)
        state["suppressed"] = state.get("suppressed", [])[-50:]
        return kept

    def audit_routing_contracts(self, state: dict[str, Any]) -> list[Incident]:
        now = int(time.time())
        last = int(state.get("routing_contract_audit_at", 0) or 0)
        if now - last < self.config.routing_contract_audit_interval_seconds:
            return []
        state["routing_contract_audit_at"] = now
        contracts = load_contracts(self.config.routing_contracts_path)
        if not contracts or not self.config.mac_profile:
            return []
        return [Incident("routing_contract", "high", finding) for finding in audit_profile(Path(self.config.mac_profile), contracts)]

    def probe_one_policy(self, state: dict[str, Any]) -> list[Incident]:
        now = int(time.time())
        last = int(state.get("policy_probe_at", 0) or 0)
        if not self.config.expected_policies or now - last < self.config.policy_probe_interval_seconds:
            return []
        index = int(state.get("policy_probe_index", 0) or 0) % len(self.config.expected_policies)
        policy = self.config.expected_policies[index]
        state["policy_probe_at"] = now
        state["policy_probe_index"] = index + 1
        result = self.client.test_policy(policy)
        ok = bool(result.get("ok")) and bool(result.get("stdout"))
        failures = state.setdefault("policy_probe_failures", {})
        if ok:
            failures.pop(policy, None)
            return []
        failures[policy] = int(failures.get(policy, 0) or 0) + 1
        if failures[policy] < self.config.policy_probe_failure_threshold:
            return []
        return [Incident("policy_probe", "high", f"线路 {policy} 连续 {failures[policy]} 次轻量探测失败", host=policy)]

    def tick(self) -> str:
        missing = self.config.missing_required()
        if missing:
            return "Surge Sentry 配置缺失：" + ", ".join(missing)

        state = self.store.load()
        events, _event_raw = self.client.dump_events()
        lines, log_path = self.read_new_log_lines(state)
        current_event_keys = [event_key(event) for event in events]

        if not state.get("initialized"):
            state["initialized"] = True
            state["seen_events"] = current_event_keys[-200:]
            self.trim_state_lists(state)
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
        self.record_background_noise(state, lines)
        incidents.extend(item for line in lines for item in [self.classify_log(line)] if item)
        incidents = self.suppress_configured_maintenance_noise(state, incidents)
        incidents.extend(self.record_recurring_noise_candidates(state, incidents))
        incidents.extend(self.audit_routing_contracts(state))

        actions: list[str] = []
        diagnostics: list[str] = []
        important = [
            item for item in incidents
            if item.severity in {"high", "medium"} and item.kind != "external_resource"
        ]
        self.update_external_resource_state(state, incidents, actions, important)
        self.update_dns_state(state, incidents, actions, important)
        important.extend(self.update_direct_failure_state(state, incidents, actions))
        important.extend(self.analyze_traffic_usage(diagnostics))
        important.extend(self.probe_one_policy(state))
        for pending in consume_pending(self.config):
            service = str(pending.get("service") or "媒体服务")
            host = str(pending.get("host") or "")
            try:
                speed = float(pending.get("sustained_mbps", 0) or 0)
            except (TypeError, ValueError, OverflowError):
                speed = 0.0
            cdn = str(pending.get("cdn") or "unknown")
            policy = str(pending.get("policy") or "unknown")
            reason = str(pending.get("reason") or "deterministic diagnosis needs escalation")
            event_id = str(pending.get("event_id") or "unknown")
            important.append(Incident(
                "media_health",
                "high" if str(pending.get("status")) == "critical" else "medium",
                f"{service} 真实媒体速度约 {speed:.1f} Mbps，CDN={cdn}，策略={policy}；{reason}；事件ID={event_id}。处理完成后执行 scripts/surge-sentry cdn-watch ack {event_id}",
                host=host,
                bypass_cooldown=True,
            ))

        suppress_proxy = self.verify_proxy_incidents(state, important, diagnostics)
        if suppress_proxy and {item.kind for item in important} == {"proxy"}:
            state["seen_events"] = list(seen)[-200:]
            self.remember_suppressed(state, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "reason": "proxy recovered during verification"})
            self.trim_state_lists(state)
            self.store.save(state)
            return '{"wakeAgent": false}'

        important = self.apply_alert_cooldown(state, important)

        if not important:
            state["seen_events"] = list(seen)[-200:]
            self.trim_state_lists(state)
            self.store.save(state)
            return '{"wakeAgent": false}'

        state["seen_events"] = list(seen)[-200:]
        self.trim_state_lists(state)
        self.store.save(state)
        return self.render_incident(important, actions, diagnostics, log_path)

    def render_incident(self, incidents: list[Incident], actions: list[str], diagnostics: list[str], log_path: Path | None) -> str:
        lines = [
            "Surge Sentry 发现需要分析的异常",
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
            "【分析要求】",
            "- 判断这是临时波动、已自动修复的问题，还是需要用户决策的问题。",
            "- 如果无需通知用户，最终回复必须只包含 [SILENT] 六个字符，不能附加解释、代码块或大小写变体。",
            "- 不要写“说明 + [SILENT]”；只要除 [SILENT] 之外还有任何字符，系统就可能把它投递给用户。",
            "- 永久修改 profile、重启 Surge、修改证书/DNS/服务器时，只能给方案并请求确认。",
            "- 需要通知时，用简短中文标题开头，下面写 2-4 条要点；只说发生了什么、已处理什么、是否需要确认。",
            "- 不要加入格式说明、任务管理提示或括号里的解释性后缀。",
            "- 如果有可复用经验，再加一行“可沉淀：...”；没有就不要写。",
        ])
        return "\n".join(lines)
