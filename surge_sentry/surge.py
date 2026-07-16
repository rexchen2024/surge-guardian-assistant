from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Iterator


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

    def dump_requests(self) -> tuple[dict[str, Any], dict[str, Any]]:
        data, result = self.raw_json("dump", "request", timeout=10)
        return (data if isinstance(data, dict) else {}), result

    def dump_dns(self) -> tuple[dict[str, Any], dict[str, Any]]:
        data, result = self.raw_json("dump", "dns", timeout=10)
        return (data if isinstance(data, dict) else {}), result

    def dump_profile_text(self, mode: str = "original") -> tuple[str, dict[str, Any]]:
        data, result = self.raw_json("dump", "profile", mode, timeout=10)
        if not isinstance(data, dict):
            return "", result
        key = "originalProfile" if mode == "original" else "profile"
        return str(data.get(key) or data.get("profile") or ""), result

    def external_resource_update_all(self) -> dict[str, Any]:
        return self.raw("external-resource", "update", "all", timeout=60)

    def flush_dns(self) -> dict[str, Any]:
        return self.raw("flush", "dns", timeout=10)

    def reload(self) -> dict[str, Any]:
        return self.raw("reload", timeout=20)

    def test_policy(self, policy: str) -> dict[str, Any]:
        return self.raw("test-policy", policy, timeout=20)

    def test_group(self, group: str) -> dict[str, Any]:
        return self.raw("test-group", group, timeout=20)

    def add_temp_rule(self, rule: str) -> dict[str, Any]:
        return self.raw("add-temp-rule", rule, timeout=10)

    def del_temp_rule(self, rule: str) -> dict[str, Any]:
        return self.raw("del-temp-rule", rule, timeout=10)

    def watch_request_updates(
        self,
        *,
        poll_interval: float = 2.0,
        idle_interval: float = 10.0,
        reconnect_delay: float = 2.0,
        is_target: Any = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield active request counters with adaptive, short-lived CLI polls.

        A persistent interactive ``surge-cli`` process retains substantial
        memory over time. Poll only ``dump active`` instead: use a quiet idle
        interval, then switch to the faster interval while a configured media
        request is active. Connection counters remain incremental in trackers.
        """
        last_controller_at = 0.0
        last_controller_latency_ms = 0.0
        last_request_at = 0.0
        stop_requested = should_stop or (lambda: False)
        while not stop_requested():
            started = time.monotonic()
            data, result = self.raw_json("dump", "active", timeout=10)
            now = time.time()
            rows = data.get("requests", []) if isinstance(data, dict) else []
            ok = bool(result.get("ok")) and isinstance(rows, list)
            target_active = False
            if ok:
                last_controller_at = now
                last_controller_latency_ms = (time.monotonic() - started) * 1000
                for item in rows:
                    if not isinstance(item, dict):
                        continue
                    last_request_at = now
                    if callable(is_target) and is_target(item):
                        target_active = True
                    yield item
            yield {
                "_tick": now,
                "_poll_ok": ok,
                "_target_active": target_active,
                "_last_request_at": last_request_at,
                "_controller_at": last_controller_at,
                "_controller_latency_ms": last_controller_latency_ms,
            }
            delay = max(0.5, poll_interval if target_active else idle_interval)
            if not ok:
                delay = max(delay, reconnect_delay)
            deadline = time.monotonic() + delay
            while time.monotonic() < deadline and not stop_requested():
                time.sleep(min(0.2, deadline - time.monotonic()))


def latest_surge_log(log_dir: Path) -> Path | None:
    if not log_dir.exists():
        return None
    files = sorted(log_dir.glob("Surge-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None
