from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class SurgeClient:
    def __init__(self, surge_cli: str):
        self.surge_cli = surge_cli

    def run(self, *args: str, timeout: int = 20) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                [self.surge_cli, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
            return {
                "ok": proc.returncode == 0,
                "code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
        except Exception as exc:
            return {"ok": False, "code": -1, "stdout": "", "stderr": str(exc)}

    def raw(self, *args: str, timeout: int = 20) -> dict[str, Any]:
        return self.run("--raw", *args, timeout=timeout)

    def raw_json(self, *args: str, timeout: int = 20) -> tuple[Any, dict[str, Any]]:
        result = self.raw(*args, timeout=timeout)
        text = result.get("stdout") or ""
        if not result["ok"] or not text or text == "(null)":
            return None, result
        try:
            return json.loads(text), result
        except Exception as exc:
            result["ok"] = False
            result["stderr"] = f"json parse failed: {exc}"
            return None, result

    def check_profile(self, path: str) -> dict[str, Any]:
        return self.run("--check", path, timeout=20)

    def dump_events(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        data, result = self.raw_json("dump", "event", timeout=10)
        if isinstance(data, dict):
            return data.get("events", []) or [], result
        return [], result

    def dump_policy(self) -> tuple[dict[str, Any], dict[str, Any]]:
        data, result = self.raw_json("dump", "policy", timeout=10)
        return (data if isinstance(data, dict) else {}), result

    def dump_rules(self) -> tuple[dict[str, Any], dict[str, Any]]:
        data, result = self.raw_json("dump", "rule", timeout=10)
        return (data if isinstance(data, dict) else {}), result

    def dump_environment(self) -> tuple[dict[str, Any], dict[str, Any]]:
        data, result = self.raw_json("environment", timeout=10)
        return (data if isinstance(data, dict) else {}), result

    def external_resource_update_all(self) -> dict[str, Any]:
        return self.raw("external-resource", "update", "all", timeout=60)

    def flush_dns(self) -> dict[str, Any]:
        return self.raw("flush", "dns", timeout=10)

    def test_policy(self, policy: str) -> dict[str, Any]:
        return self.raw("test-policy", policy, timeout=20)

    def test_group(self, group: str) -> dict[str, Any]:
        return self.raw("test-group", group, timeout=20)

    def add_temp_rule(self, rule: str) -> dict[str, Any]:
        return self.raw("add-temp-rule", rule, timeout=10)

    def del_temp_rule(self, rule: str) -> dict[str, Any]:
        return self.raw("del-temp-rule", rule, timeout=10)


def latest_surge_log(log_dir: Path) -> Path | None:
    if not log_dir.exists():
        return None
    files = sorted(log_dir.glob("Surge-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None
