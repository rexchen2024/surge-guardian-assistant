from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SURGE_CLI = "/Applications/Surge.app/Contents/Applications/surge-cli"


def _expand(value: str) -> str:
    return os.path.expandvars(value).replace("~", str(Path.home()))


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
    lines = ["# Local config for surge-hermes-guardian. Do not commit this file.", ""]
    for key in sorted(values):
        value = values[key]
        if any(ch.isspace() for ch in value):
            value = value.replace('"', '\\"')
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n")


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class GuardianConfig:
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

    @classmethod
    def load(cls, root: Path) -> "GuardianConfig":
        env_path = root / ".env"
        env = read_env(env_path)
        return cls(
            root=root,
            env_path=env_path,
            surge_cli=env.get("SURGE_CLI") or shutil.which("surge-cli") or DEFAULT_SURGE_CLI,
            surge_log_dir=Path(_expand(env.get("SURGE_LOG_DIR", "${HOME}/Library/Logs/Surge"))),
            state_dir=Path(_expand(env.get("STATE_DIR", "${HOME}/.hermes/state/surge-hermes-guardian"))),
            expected_policies=split_csv(env.get("EXPECTED_POLICIES", "")),
            proxy_policy=env.get("PROXY_POLICY", "Proxy"),
            check_domain=env.get("CHECK_DOMAIN", ""),
            check_ip=env.get("CHECK_IP", ""),
            mac_profile=env.get("MAC_PROFILE", ""),
            mobile_profile=env.get("MOBILE_PROFILE", ""),
            direct_fail_window_seconds=int(env.get("DIRECT_FAIL_WINDOW_SECONDS", "900") or "900"),
            temp_rule_review_seconds=int(env.get("TEMP_RULE_REVIEW_SECONDS", "43200") or "43200"),
            external_resource_fail_threshold=int(env.get("EXTERNAL_RESOURCE_FAIL_THRESHOLD", "2") or "2"),
            dns_fail_threshold=int(env.get("DNS_FAIL_THRESHOLD", "5") or "5"),
            direct_fail_threshold=int(env.get("DIRECT_FAIL_THRESHOLD", "3") or "3"),
            policy_recovered_alert_threshold=int(env.get("POLICY_RECOVERED_ALERT_THRESHOLD", "3") or "3"),
        )

    def missing_required(self) -> list[str]:
        missing = []
        if not self.expected_policies:
            missing.append("EXPECTED_POLICIES")
        if not self.proxy_policy:
            missing.append("PROXY_POLICY")
        return missing
