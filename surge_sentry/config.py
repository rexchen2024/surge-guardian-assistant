from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SURGE_CLI = "/Applications/Surge.app/Contents/Applications/surge-cli"


def _expand(value: str) -> str:
    expanded = os.path.expandvars(value)
    if expanded == "~" or expanded.startswith("~/"):
        return str(Path.home()) + expanded[1:]
    return expanded


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        try:
            parts = shlex.split(value, posix=True)
            value = parts[0] if parts else ""
        except ValueError:
            value = value.strip("\"'")
        values[key] = _expand(value)
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    lines = ["# Local config for surge-sentry. Do not commit this file.", ""]
    for key in sorted(values):
        value = values[key]
        if any(ch.isspace() for ch in value):
            value = value.replace('"', '\\"')
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o600)


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_bool(value: str, default: bool = False) -> bool:
    text = value.strip().lower()
    if not text:
        return default
    return text not in {"0", "false", "no", "off"}


_WEEKDAYS = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def _parse_hhmm(value: str) -> int:
    hour_text, minute_text = value.strip().split(":", 1)
    hour = int(hour_text)
    minute = int(minute_text)
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(value)
    return hour * 60 + minute


def parse_maintenance_windows(value: str) -> list[dict[str, Any]]:
    """Parse optional recurring local maintenance windows.

    Format:
      thu 05:00-05:10:dns,direct_domain_failure,proxy; sun 03:00-03:20:dns
    """
    windows: list[dict[str, Any]] = []
    for raw in value.split(";"):
        item = raw.strip()
        if not item:
            continue
        day_and_range, _, kinds_text = item.rpartition(":")
        if not day_and_range:
            day_and_range = kinds_text
            kinds_text = ""
        day_text, time_range = day_and_range.split(None, 1)
        start_text, end_text = time_range.split("-", 1)
        weekday = _WEEKDAYS[day_text.strip().lower()]
        kinds = split_csv(kinds_text) if kinds_text else ["dns", "direct_domain_failure", "proxy"]
        windows.append({
            "weekday": weekday,
            "start_minute": _parse_hhmm(start_text),
            "end_minute": _parse_hhmm(end_text),
            "kinds": kinds,
        })
    return windows


@dataclass(frozen=True)
class SentryConfig:
    root: Path
    env_path: Path
    surge_cli: str
    surge_log_dir: Path
    state_dir: Path
    expected_policies: list[str]
    proxy_policy: str
    check_domain: str
    check_ip: str
    mac_profile: str
    mobile_profile: str
    direct_fail_window_seconds: int
    temp_rule_review_seconds: int
    external_resource_fail_threshold: int
    dns_fail_threshold: int
    direct_fail_threshold: int
    policy_recovered_alert_threshold: int
    alert_cooldown_seconds: int
    maintenance_windows: list[dict[str, Any]]
    recurring_noise_bucket_minutes: int
    recurring_noise_min_occurrences: int
    recurring_noise_history_days: int
    auto_update: bool
    auto_update_interval_seconds: int
    traffic_analysis_enabled: bool
    traffic_stat_dir: Path
    traffic_policy_patterns: list[str]
    traffic_monthly_cap_gb: float
    traffic_reset_day: int
    traffic_daily_warn_ratio: float
    traffic_daily_critical_ratio: float
    traffic_direct_host_patterns: list[str]
    traffic_direct_leak_min_gb: float

    @classmethod
    def load(cls, root: Path) -> "SentryConfig":
        env_path = root / ".env"
        env = read_env(env_path)
        return cls(
            root=root,
            env_path=env_path,
            surge_cli=env.get("SURGE_CLI") or shutil.which("surge-cli") or DEFAULT_SURGE_CLI,
            surge_log_dir=Path(_expand(env.get("SURGE_LOG_DIR", "${HOME}/Library/Logs/Surge"))),
            state_dir=Path(_expand(env.get("STATE_DIR", "${HOME}/.hermes/state/surge-sentry"))),
            expected_policies=split_csv(env.get("EXPECTED_POLICIES", "")),
            proxy_policy=env.get("PROXY_POLICY", "Proxy"),
            check_domain=env.get("CHECK_DOMAIN", ""),
            check_ip=env.get("CHECK_IP", ""),
            mac_profile=env.get("MAC_PROFILE", ""),
            mobile_profile=env.get("MOBILE_PROFILE", ""),
            direct_fail_window_seconds=int(env.get("DIRECT_FAIL_WINDOW_SECONDS", "900") or "900"),
            temp_rule_review_seconds=int(env.get("TEMP_RULE_REVIEW_SECONDS", "43200") or "43200"),
            external_resource_fail_threshold=int(env.get("EXTERNAL_RESOURCE_FAIL_THRESHOLD", "2") or "2"),
            dns_fail_threshold=int(env.get("DNS_FAIL_THRESHOLD", "10") or "10"),
            direct_fail_threshold=int(env.get("DIRECT_FAIL_THRESHOLD", "3") or "3"),
            policy_recovered_alert_threshold=int(env.get("POLICY_RECOVERED_ALERT_THRESHOLD", "3") or "3"),
            alert_cooldown_seconds=int(env.get("ALERT_COOLDOWN_SECONDS", "3600") or "3600"),
            maintenance_windows=parse_maintenance_windows(env.get("MAINTENANCE_WINDOWS", "")),
            recurring_noise_bucket_minutes=int(env.get("RECURRING_NOISE_BUCKET_MINUTES", "10") or "10"),
            recurring_noise_min_occurrences=int(env.get("RECURRING_NOISE_MIN_OCCURRENCES", "3") or "3"),
            recurring_noise_history_days=int(env.get("RECURRING_NOISE_HISTORY_DAYS", "35") or "35"),
            auto_update=parse_bool(env.get("AUTO_UPDATE", "1"), True),
            auto_update_interval_seconds=int(env.get("AUTO_UPDATE_INTERVAL_SECONDS", "86400") or "86400"),
            traffic_analysis_enabled=parse_bool(env.get("TRAFFIC_ANALYSIS_ENABLED", "0")),
            traffic_stat_dir=Path(_expand(env.get(
                "TRAFFIC_STAT_DIR",
                "${HOME}/Library/Application Support/com.nssurge.surge-mac/TrafficStatData",
            ))),
            traffic_policy_patterns=split_csv(env.get("TRAFFIC_POLICY_PATTERNS", "")),
            traffic_monthly_cap_gb=float(env.get("TRAFFIC_MONTHLY_CAP_GB", "0") or "0"),
            traffic_reset_day=int(env.get("TRAFFIC_RESET_DAY", "1") or "1"),
            traffic_daily_warn_ratio=float(env.get("TRAFFIC_DAILY_WARN_RATIO", "1.2") or "1.2"),
            traffic_daily_critical_ratio=float(env.get("TRAFFIC_DAILY_CRITICAL_RATIO", "2.0") or "2.0"),
            traffic_direct_host_patterns=split_csv(env.get("TRAFFIC_DIRECT_HOST_PATTERNS", "")),
            traffic_direct_leak_min_gb=float(env.get("TRAFFIC_DIRECT_LEAK_MIN_GB", "1") or "1"),
        )

    def missing_required(self) -> list[str]:
        missing = []
        if not self.expected_policies:
            missing.append("EXPECTED_POLICIES")
        if not self.proxy_policy:
            missing.append("PROXY_POLICY")
        return missing
