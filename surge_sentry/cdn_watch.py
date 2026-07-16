from __future__ import annotations

import fnmatch
import hashlib
import ipaddress
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .config import SentryConfig
from .state import StateStore
from .surge import SurgeClient


MB = 1024 * 1024
HEARTBEAT_WRITE_SECONDS = 30
WATCH_STALE_SECONDS = 90
MAX_HISTORY_LINES = 2000
MAX_BACKUPS = 12
MAX_PROCESSED_EVENTS = 100
PENDING_RETRY_SECONDS = 600
RESTART_REMINDER_SECONDS = 180
FASTLY_NETWORKS = tuple(ipaddress.ip_network(item) for item in (
    "146.75.0.0/16",
    "151.101.0.0/16",
    "199.232.0.0/16",
))


def extract_host(value: str) -> str:
    text = str(value or "").strip().lower()
    if "://" in text:
        text = text.split("://", 1)[1]
    text = text.split("/", 1)[0]
    if text.startswith("[") and "]" in text:
        return text[1:text.index("]")]
    if text.count(":") == 1 and text.rsplit(":", 1)[1].isdigit():
        text = text.rsplit(":", 1)[0]
    return text.rstrip(".")


def is_direct_policy(value: str) -> bool:
    text = str(value or "").strip().lower().replace(" ", "")
    return text in {"direct", "直连", "direct-direct"}


def policy_group_from_notes(notes: Any) -> str:
    if not isinstance(notes, list):
        return ""
    for note in notes:
        marker = "Policy decision path:"
        text = str(note)
        if marker not in text:
            continue
        path = text.split(marker, 1)[1].strip()
        return path.split("->", 1)[0].strip()
    return ""


def _plain_ip(remote_address: str) -> str:
    text = str(remote_address or "").split(" ", 1)[0].strip()
    if text.startswith("[") and "]" in text:
        return text[1:text.index("]")]
    if text.count(":") == 1 and text.rsplit(":", 1)[1].isdigit():
        return text.rsplit(":", 1)[0]
    return text


def classify_cdn(remote_address: str = "", dns_path: str = "") -> str:
    path = str(dns_path or "").lower()
    if "fastly" in path:
        return "fastly"
    if any(token in path for token in ("akamai", "edgesuite.net", "edgekey.net", "akamaiedge.net")):
        return "akamai"
    if any(token in path for token in (
        "ks-cdn.com", "ksyuncdn.com", "cdngslb.com", "alikunlun.com", "qtlcdn.com",
    )):
        return "china-partner"
    if "(proxy)" in str(remote_address or "").lower():
        return "proxy"
    try:
        address = ipaddress.ip_address(_plain_ip(remote_address))
    except ValueError:
        address = None
    if address and any(address in network for network in FASTLY_NETWORKS):
        return "fastly"
    if address and address.version == 4 and address in ipaddress.ip_network("17.0.0.0/8"):
        return "apple"
    if any(token in path for token in ("g.aaplimg.com", "apple-dns.net")):
        return "apple"
    return "unknown"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value or 0)
        return result if result == result and result not in {float("inf"), float("-inf")} else default
    except (TypeError, ValueError, OverflowError):
        return default


def _validated_exact_host(value: Any) -> str:
    host = str(value or "").strip().lower().rstrip(".")
    if len(host) > 253 or "*" in host or not re.fullmatch(
        r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
        host,
    ):
        raise ValueError("autofix DNS host must be an exact valid hostname")
    return host


def _validated_resolver(value: Any) -> str:
    text = str(value or "").strip()
    try:
        return str(ipaddress.ip_address(text))
    except ValueError as exc:
        raise ValueError("autofix resolver must be a literal IPv4 or IPv6 address") from exc


def resolver_label(server: str) -> str:
    text = str(server or "").lower()
    if "1.1.1.1" in text or "cloudflare" in text:
        return "cloudflare"
    if "8.8.8.8" in text or "8.8.4.4" in text or "google" in text:
        return "google"
    if "alidns" in text or "doh.pub" in text or "223.5.5.5" in text:
        return "domestic"
    return "other" if text else "unknown"


@dataclass(frozen=True)
class AutoFixSpec:
    enabled: bool = False
    dns_overrides: dict[str, str] = field(default_factory=dict)
    trigger_cdns: tuple[str, ...] = ("fastly",)
    expected_cdn: str = ""
    reload: bool = True
    rollback_on_failure: bool = True


@dataclass(frozen=True)
class ServiceSpec:
    identifier: str
    name: str
    host_patterns: tuple[str, ...]
    group_names: tuple[str, ...] = ()
    window_seconds: float = 30.0
    idle_seconds: float = 15.0
    health_mbps: float = 20.0
    usable_mbps: float = 10.0
    critical_mbps: float = 3.0
    degraded_seconds: float = 30.0
    critical_seconds: float = 20.0
    min_transfer_mb: float = 0.5
    cooldown_seconds: int = 900
    autofix: AutoFixSpec = field(default_factory=AutoFixSpec)

    def matches(self, host: str) -> bool:
        text = host.lower()
        return any(fnmatch.fnmatch(text, pattern.lower()) for pattern in self.host_patterns)


@dataclass(frozen=True)
class WatchSettings:
    poll_interval_seconds: float
    notify_target: str
    services: tuple[ServiceSpec, ...]


def load_watch_settings(path: Path) -> WatchSettings:
    if path.is_symlink():
        raise ValueError("cdn-watch config must not be a symlink")
    if not path.is_file():
        raise ValueError("cdn-watch config is missing or not a regular file")
    if path.stat().st_uid != os.getuid():
        raise ValueError("cdn-watch config must be owned by the current user")
    path.chmod(0o600)
    data = json.loads(path.read_text())
    defaults = data.get("defaults", {}) if isinstance(data.get("defaults"), dict) else {}
    services: list[ServiceSpec] = []
    identifiers: set[str] = set()
    for raw in data.get("services", []):
        if not isinstance(raw, dict) or not raw.get("id") or not raw.get("host_patterns"):
            continue
        values = {**defaults, **raw}
        raw_fix = values.get("autofix", {}) if isinstance(values.get("autofix"), dict) else {}
        overrides: dict[str, str] = {}
        for host, server in (raw_fix.get("dns_overrides", {}) or {}).items():
            overrides[_validated_exact_host(host)] = _validated_resolver(server)
        identifier = str(values["id"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", identifier):
            raise ValueError("service id contains unsupported characters")
        if identifier in identifiers:
            raise ValueError("service id must be unique")
        identifiers.add(identifier)
        numeric = {
            "window_seconds": float(values.get("window_seconds", 30)),
            "idle_seconds": float(values.get("idle_seconds", 15)),
            "health_mbps": float(values.get("health_mbps", 20)),
            "usable_mbps": float(values.get("usable_mbps", 10)),
            "critical_mbps": float(values.get("critical_mbps", 3)),
            "degraded_seconds": float(values.get("degraded_seconds", 30)),
            "critical_seconds": float(values.get("critical_seconds", 20)),
            "min_transfer_mb": float(values.get("min_transfer_mb", 0.5)),
        }
        if any(not math.isfinite(value) or value <= 0 for value in numeric.values()):
            raise ValueError("cdn-watch thresholds must be finite positive numbers")
        if not numeric["health_mbps"] > numeric["usable_mbps"] > numeric["critical_mbps"]:
            raise ValueError("speed thresholds must satisfy health > usable > critical")
        cooldown_seconds = int(values.get("cooldown_seconds", 900))
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must not be negative")
        autofix_enabled = bool(raw_fix.get("enabled", False))
        autofix_reload = bool(raw_fix.get("reload", True))
        trigger_cdns = tuple(str(item) for item in raw_fix.get("trigger_cdns", ["fastly"]) if str(item))
        expected_cdn = str(raw_fix.get("expected_cdn", ""))
        if autofix_enabled and (not overrides or not trigger_cdns or not expected_cdn):
            raise ValueError("enabled autofix requires exact DNS overrides, trigger CDNs, and expected CDN")
        if autofix_enabled and not autofix_reload:
            raise ValueError("enabled autofix requires reload=true for runtime verification")
        services.append(ServiceSpec(
            identifier=identifier,
            name=str(values.get("name") or values["id"]),
            host_patterns=tuple(str(item) for item in values.get("host_patterns", [])),
            group_names=tuple(str(item) for item in values.get("group_names", [])),
            window_seconds=numeric["window_seconds"],
            idle_seconds=numeric["idle_seconds"],
            health_mbps=numeric["health_mbps"],
            usable_mbps=numeric["usable_mbps"],
            critical_mbps=numeric["critical_mbps"],
            degraded_seconds=numeric["degraded_seconds"],
            critical_seconds=numeric["critical_seconds"],
            min_transfer_mb=numeric["min_transfer_mb"],
            cooldown_seconds=cooldown_seconds,
            autofix=AutoFixSpec(
                enabled=autofix_enabled,
                dns_overrides=overrides,
                trigger_cdns=trigger_cdns,
                expected_cdn=expected_cdn,
                reload=autofix_reload,
                rollback_on_failure=bool(raw_fix.get("rollback_on_failure", True)),
            ),
        ))
    if not services:
        raise ValueError("cdn-watch config has no valid services")
    poll_interval = float(data.get("poll_interval_seconds", 2))
    if not math.isfinite(poll_interval) or poll_interval < 1:
        raise ValueError("poll_interval_seconds must be a finite number of at least 1")
    return WatchSettings(
        poll_interval_seconds=poll_interval,
        notify_target=str(data.get("notify_target") or "telegram"),
        services=tuple(services),
    )


@dataclass(frozen=True)
class HealthOutcome:
    status: str
    service_id: str
    service_name: str
    sustained_mbps: float
    average_mbps: float
    peak_mbps: float
    transferred_mb: float
    duration_seconds: float
    host: str
    cdn: str
    policy: str
    policy_group: str
    newest_start_date: float


class ServiceTracker:
    def __init__(self, spec: ServiceSpec):
        self.spec = spec
        self.connections: dict[str, dict[str, Any]] = {}
        self.samples: deque[dict[str, Any]] = deque()
        self.session_started_at = 0.0
        self.last_activity_at = 0.0

    def ingest(self, event: dict[str, Any], now: float) -> bool:
        host = extract_host(str(event.get("remoteHost") or event.get("URL") or ""))
        if not host or not self.spec.matches(host):
            return False
        group = policy_group_from_notes(event.get("notes"))
        if self.spec.group_names and group and group not in self.spec.group_names:
            return False

        connection_id = str(event.get("id") or "")
        if not connection_id:
            return False
        in_bytes = max(0, _safe_int(event.get("inBytes")))
        current_bps = max(0.0, _safe_float(event.get("inCurrentSpeed")))
        prior = self.connections.get(connection_id)
        delta = max(0, in_bytes - _safe_int(prior.get("in_bytes"))) if prior else 0
        elapsed = max(0.25, now - _safe_float(prior.get("seen_at"), now)) if prior else 1.0
        delta_mbps = delta * 8 / elapsed / 1_000_000
        current_mbps = current_bps * 8 / 1_000_000
        sample_mbps = max(delta_mbps, current_mbps)
        remote_address = str(event.get("remoteAddress") or "")
        policy = str(event.get("policyName") or event.get("originalPolicyName") or "")
        cdn = classify_cdn(remote_address)
        start_date = _safe_float(event.get("startDate"))

        self.connections[connection_id] = {
            "in_bytes": in_bytes,
            "seen_at": now,
            "host": host,
            "cdn": cdn,
            "policy": policy,
            "policy_group": group,
            "start_date": start_date,
        }
        if bool(event.get("completed")) or str(event.get("status", "")).lower() in {"completed", "failed"}:
            self.connections.pop(connection_id, None)

        if delta <= 0 and sample_mbps <= 0:
            return True
        if not self.session_started_at or now - self.last_activity_at > self.spec.idle_seconds:
            self.session_started_at = now
            self.samples.clear()
        self.last_activity_at = now
        self.samples.append({
            "time": now,
            "bytes": delta,
            "mbps": sample_mbps,
            "host": host,
            "cdn": cdn,
            "policy": policy,
            "policy_group": group,
            "start_date": start_date,
        })
        return True

    def evaluate(self, now: float) -> HealthOutcome:
        cutoff = now - self.spec.window_seconds
        while self.samples and _safe_float(self.samples[0]["time"]) < cutoff:
            self.samples.popleft()
        if not self.samples or now - self.last_activity_at > self.spec.idle_seconds:
            return HealthOutcome(
                "idle", self.spec.identifier, self.spec.name, 0, 0, 0, 0, 0, "", "unknown", "", "", 0,
            )

        duration = max(0.0, now - self.session_started_at)
        transferred = sum(_safe_int(item["bytes"]) for item in self.samples)
        speeds = sorted(_safe_float(item["mbps"]) for item in self.samples if _safe_float(item["mbps"]) > 0)
        active_span = max(1.0, min(duration or 1.0, self.spec.window_seconds))
        average = transferred * 8 / active_span / 1_000_000
        peak = max(speeds, default=0.0)
        p75 = speeds[int((len(speeds) - 1) * 0.75)] if speeds else 0.0
        sustained = max(average, p75)
        transferred_mb = transferred / MB
        latest = self.samples[-1]

        if sustained >= self.spec.health_mbps:
            status = "healthy"
        elif sustained >= self.spec.usable_mbps:
            status = "usable"
        elif (
            duration >= self.spec.critical_seconds
            and transferred_mb >= self.spec.min_transfer_mb
            and sustained < self.spec.critical_mbps
        ):
            status = "critical"
        elif duration >= self.spec.degraded_seconds and transferred_mb >= self.spec.min_transfer_mb:
            status = "degraded"
        else:
            status = "observing"

        host_weights: Counter[str] = Counter()
        for item in self.samples:
            host_weights[str(item.get("host") or "")] += max(1, _safe_int(item.get("bytes")))
        problem_host = host_weights.most_common(1)[0][0] if host_weights else str(latest.get("host") or "")
        host_samples = [item for item in self.samples if str(item.get("host") or "") == problem_host]
        host_latest = host_samples[-1] if host_samples else latest
        cdns = Counter(str(item["cdn"]) for item in host_samples if item.get("cdn") not in {"", "unknown"})
        cdn = cdns.most_common(1)[0][0] if cdns else str(host_latest.get("cdn") or "unknown")
        return HealthOutcome(
            status=status,
            service_id=self.spec.identifier,
            service_name=self.spec.name,
            sustained_mbps=sustained,
            average_mbps=average,
            peak_mbps=peak,
            transferred_mb=transferred_mb,
            duration_seconds=duration,
            host=problem_host,
            cdn=cdn,
            policy=str(host_latest.get("policy") or ""),
            policy_group=str(host_latest.get("policy_group") or ""),
            newest_start_date=max(_safe_float(item.get("start_date")) for item in host_samples or self.samples),
        )


@dataclass(frozen=True)
class EditResult:
    ok: bool
    changed: bool
    backup_path: str = ""
    message: str = ""


class ProfileEditor:
    def __init__(self, client: SurgeClient, state_dir: Path):
        self.client = client
        self.backup_dir = state_dir / "cdn-watch-backups"

    def _runtime_has_overrides(self, overrides: dict[str, str]) -> tuple[bool, str]:
        try:
            text, result = self.client.dump_profile_text("original")
        except Exception:
            return False, "active Surge profile could not be inspected"
        if not result.get("ok") or not text:
            return False, "active Surge profile could not be inspected"
        for host, resolver in overrides.items():
            pattern = rf"(?im)^\s*{re.escape(host)}\s*=\s*server:\s*{re.escape(resolver)}\s*$"
            if not re.search(pattern, text):
                return False, f"active Surge profile does not contain verified override for {host}"
        return True, "active Surge profile contains verified overrides"

    @staticmethod
    def _profile_identity(text: str) -> tuple[tuple[str, str], ...]:
        """Return a secret-free structural fingerprint for an original profile."""
        section = ""
        identity: list[tuple[str, str]] = []
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line.lower()
                continue
            if not line or line.startswith(("#", ";")) or section == "[mitm]":
                continue
            if section == "[rule]":
                parts = [item.strip() for item in line.split(",")]
                key = ",".join(parts[:2])
            else:
                key = line.split("=", 1)[0].strip() if "=" in line else line
            identity.append((section, key))
        return tuple(identity)

    @staticmethod
    def _host_directives(text: str) -> dict[str, str]:
        section = ""
        directives: dict[str, str] = {}
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line.lower()
                continue
            if section != "[host]" or not line or line.startswith(("#", ";")) or "=" not in line:
                continue
            host, value = line.split("=", 1)
            directives[extract_host(host)] = re.sub(r"\s+", "", value.lower())
        return directives

    def _runtime_matches_host_state(self, expected_text: str, hosts: set[str]) -> tuple[bool, str]:
        try:
            runtime_text, result = self.client.dump_profile_text("original")
        except Exception:
            return False, "active Surge profile could not be inspected after rollback"
        if not result.get("ok") or not runtime_text:
            return False, "active Surge profile could not be inspected after rollback"
        expected = self._host_directives(expected_text)
        runtime = self._host_directives(runtime_text)
        for host in hosts:
            if runtime.get(host) != expected.get(host):
                return False, f"active Surge profile did not restore host state for {host}"
        return True, "active Surge profile rollback verified"

    def _restore_text(
        self,
        profile: Path,
        text: str,
        mode: int,
        hosts: set[str],
        *,
        reload_profile: bool,
    ) -> tuple[bool, str]:
        candidate = profile.parent / f".{profile.name}.cdn-watch-restore.conf"
        candidate.write_text(text)
        candidate.chmod(mode)
        candidate.replace(profile)
        reload_ok = True
        if reload_profile:
            reload_ok = bool(self.client.reload().get("ok"))
        verified, detail = self._runtime_matches_host_state(text, hosts)
        flush_ok = bool(self.client.flush_dns().get("ok")) if verified else False
        if not verified:
            return False, detail
        if not flush_ok:
            return False, "original profile restored, but DNS flush failed"
        if not reload_ok:
            return True, "original profile and active host state restored; reload command reported failure"
        return True, "original profile and active host state restored"

    def _trim_backups(self) -> None:
        files = sorted(self.backup_dir.glob("*.conf"), key=lambda item: item.stat().st_mtime, reverse=True)
        for path in files[MAX_BACKUPS:]:
            path.unlink(missing_ok=True)

    @staticmethod
    def updated_host_section(text: str, overrides: dict[str, str]) -> str:
        lines = text.splitlines()
        start = next((idx for idx, line in enumerate(lines) if line.strip().lower() == "[host]"), -1)
        if start < 0:
            suffix = "" if not lines or not lines[-1].strip() else "\n"
            block = ["[Host]", *(f"{host} = server:{server}" for host, server in overrides.items())]
            return "\n".join(lines) + suffix + "\n".join(block) + "\n"
        end = next(
            (idx for idx in range(start + 1, len(lines)) if lines[idx].strip().startswith("[") and lines[idx].strip().endswith("]")),
            len(lines),
        )
        found: set[str] = set()
        for idx in range(start + 1, end):
            line = lines[idx]
            if not line.strip() or line.lstrip().startswith(("#", ";")) or "=" not in line:
                continue
            host = extract_host(line.split("=", 1)[0].strip())
            if host not in overrides:
                continue
            lines[idx] = f"{host} = server:{overrides[host]}"
            found.add(host)
        missing = [host for host in overrides if host not in found]
        if missing:
            lines[end:end] = [f"{host} = server:{overrides[host]}" for host in missing]
        return "\n".join(lines) + "\n"

    def ensure(self, profile: Path, overrides: dict[str, str], *, reload_profile: bool) -> EditResult:
        if not profile.exists():
            return EditResult(False, False, message="profile missing")
        if profile.is_symlink() or not profile.is_file():
            return EditResult(False, False, message="profile must be a regular non-symlink file")
        try:
            runtime_text, runtime_result = self.client.dump_profile_text("original")
        except Exception:
            return EditResult(False, False, message="active Surge profile could not be inspected")
        if not runtime_result.get("ok") or not runtime_text:
            return EditResult(False, False, message="active Surge profile could not be inspected")
        original = profile.read_text()
        if self._profile_identity(runtime_text) != self._profile_identity(original):
            return EditResult(False, False, message="configured profile does not match the active Surge profile")
        original_mode = profile.stat().st_mode & 0o777
        updated = self.updated_host_section(original, overrides)
        if updated == original:
            verified, detail = self._runtime_has_overrides(overrides)
            if not verified and reload_profile and self.client.reload().get("ok"):
                verified, detail = self._runtime_has_overrides(overrides)
            if not verified:
                return EditResult(False, False, message=detail)
            flush = self.client.flush_dns()
            return EditResult(bool(flush.get("ok")), False, message="override already present; DNS cache refreshed")

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = self.backup_dir / f"{profile.stem}-{stamp}.conf"
        backup.write_text(original)
        backup.chmod(0o600)
        self._trim_backups()
        candidate = profile.parent / f".{profile.name}.cdn-watch-candidate.conf"
        candidate.write_text(updated)
        candidate.chmod(original_mode)
        checked = self.client.check_profile(str(candidate))
        if not checked.get("ok"):
            candidate.unlink(missing_ok=True)
            return EditResult(False, False, str(backup), "candidate profile check failed")
        try:
            current = profile.read_text()
        except OSError:
            candidate.unlink(missing_ok=True)
            return EditResult(False, False, str(backup), "profile disappeared during repair")
        if hashlib.sha256(current.encode("utf-8")).digest() != hashlib.sha256(original.encode("utf-8")).digest():
            candidate.unlink(missing_ok=True)
            return EditResult(False, False, str(backup), "profile changed concurrently; repair aborted")
        candidate.replace(profile)
        if reload_profile:
            reloaded = self.client.reload()
            if not reloaded.get("ok"):
                restored, restore_detail = self._restore_text(
                    profile, original, original_mode, set(overrides), reload_profile=True,
                )
                return EditResult(False, False, str(backup), f"reload failed; {restore_detail}")
        verified, detail = self._runtime_has_overrides(overrides)
        if not verified:
            _restored, restore_detail = self._restore_text(
                profile, original, original_mode, set(overrides), reload_profile=reload_profile,
            )
            return EditResult(False, False, str(backup), f"runtime verification failed; {detail}; {restore_detail}")
        flushed = self.client.flush_dns()
        if not flushed.get("ok"):
            _restored, restore_detail = self._restore_text(
                profile, original, original_mode, set(overrides), reload_profile=reload_profile,
            )
            return EditResult(False, False, str(backup), f"DNS flush failed; {restore_detail}")
        return EditResult(True, True, str(backup), "profile updated and DNS cache refreshed")

    def restore(self, profile: Path, backup: Path, *, reload_profile: bool) -> EditResult:
        if not profile.exists() or not backup.exists() or profile.is_symlink() or backup.is_symlink():
            return EditResult(False, False, str(backup), "rollback material missing")
        original_mode = profile.stat().st_mode & 0o777
        current_text = profile.read_text()
        backup_text = backup.read_text()
        current_hosts = self._host_directives(current_text)
        backup_hosts = self._host_directives(backup_text)
        changed_hosts = {
            host for host in set(current_hosts) | set(backup_hosts)
            if current_hosts.get(host) != backup_hosts.get(host)
        }
        candidate = profile.parent / f".{profile.name}.cdn-watch-rollback.conf"
        candidate.write_text(backup_text)
        candidate.chmod(original_mode)
        checked = self.client.check_profile(str(candidate))
        if not checked.get("ok"):
            candidate.unlink(missing_ok=True)
            return EditResult(False, False, str(backup), "rollback profile check failed")
        candidate.replace(profile)
        reload_ok = True
        if reload_profile:
            reload_ok = bool(self.client.reload().get("ok"))
        verified, detail = self._runtime_matches_host_state(backup_text, changed_hosts)
        if not verified:
            return EditResult(False, True, str(backup), f"rollback written, but {detail}")
        if not self.client.flush_dns().get("ok"):
            return EditResult(False, True, str(backup), "rollback verified, but DNS flush failed")
        if not reload_ok:
            return EditResult(False, True, str(backup), "rollback host state verified, but reload command reported failure")
        return EditResult(True, True, str(backup), "rollback complete")


class HermesNotifier:
    def __init__(self, target: str, executable: str = ""):
        self.target = target
        self.executable = executable or shutil.which("hermes") or str(Path.home() / ".local/bin/hermes")

    def send(self, message: str) -> bool:
        try:
            result = subprocess.run(
                [self.executable, "send", "--to", self.target, "--quiet", "--file", "-"],
                input=message,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15,
            )
            return result.returncode == 0
        except Exception:
            return False


class CdnWatchDaemon:
    def __init__(
        self,
        config: SentryConfig,
        settings: WatchSettings,
        *,
        client: SurgeClient | None = None,
        notifier: HermesNotifier | None = None,
        clock: Callable[[], float] = time.time,
    ):
        self.config = config
        self.settings = settings
        self.client = client or SurgeClient(config.surge_cli)
        self.notifier = notifier or HermesNotifier(settings.notify_target)
        self.clock = clock
        self.state_store = StateStore(config.state_dir / "cdn-watch-state.json")
        self.trackers = {spec.identifier: ServiceTracker(spec) for spec in settings.services}
        self.specs = {spec.identifier: spec for spec in settings.services}
        self.editor = ProfileEditor(self.client, config.state_dir)
        self.signature = watch_signature(config)
        self.running = True
        self.event_errors = 0
        self.last_health_persist_at = 0.0

    def _is_target_event(self, event: dict[str, Any]) -> bool:
        host = extract_host(str(event.get("remoteHost") or event.get("URL") or ""))
        if not host:
            return False
        group = policy_group_from_notes(event.get("notes"))
        return any(
            spec.matches(host) and (not spec.group_names or not group or group in spec.group_names)
            for spec in self.settings.services
        )

    def _write_pending(self, outcome: HealthOutcome, reason: str) -> str:
        pending_dir = self.config.state_dir / "cdn-watch-pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        event_id = f"{int(self.clock() * 1000)}-{outcome.service_id}-{uuid4().hex[:10]}"
        path = pending_dir / f"{event_id}.json"
        StateStore(path).save({
            "event_id": event_id,
            "service": outcome.service_name,
            "host": outcome.host,
            "status": outcome.status,
            "sustained_mbps": round(outcome.sustained_mbps, 2),
            "average_mbps": round(outcome.average_mbps, 2),
            "peak_mbps": round(outcome.peak_mbps, 2),
            "cdn": outcome.cdn,
            "policy": outcome.policy,
            "reason": reason,
            "created_at": int(self.clock()),
        })
        return event_id

    def _notify_or_escalate(self, outcome: HealthOutcome, message: str, reason: str) -> bool:
        if self.notifier.send(message):
            return True
        self._write_pending(outcome, f"Telegram direct notification failed; {reason}")
        return False

    def _remind_restart_if_needed(
        self,
        outcome: HealthOutcome,
        prior: dict[str, Any],
        now: float,
    ) -> None:
        repair_at = _safe_float(prior.get("repair_at"))
        reminded_at = _safe_float(prior.get("restart_reminded_at"))
        if not repair_at or reminded_at or now - repair_at < RESTART_REMINDER_SECONDS:
            return
        self._notify_or_escalate(
            outcome,
            f"⏳ {outcome.service_name}自动修复正在等待新连接复验\n请完全退出 App 后重新打开播放，后台会自动确认结果。",
            "waiting for a post-repair connection",
        )
        self._save_service_state(outcome.service_id, {
            "phase": "awaiting_restart",
            "status": outcome.status,
            "restart_reminded_at": int(now),
        })

    def _dns_context(self, host: str, fallback_cdn: str) -> tuple[str, str]:
        data, result = self.client.dump_dns()
        if not result.get("ok"):
            return fallback_cdn, "unknown"
        for item in data.get("dnsCache", []) if isinstance(data, dict) else []:
            if extract_host(str(item.get("domain") or "")) != host:
                continue
            classified = classify_cdn(dns_path=str(item.get("path") or ""))
            cdn = fallback_cdn if classified == "unknown" else classified
            return cdn, resolver_label(str(item.get("server") or ""))
        return fallback_cdn, "unknown"

    def _record_history(self, outcome: HealthOutcome, phase: str, resolver: str = "unknown") -> None:
        path = self.config.state_dir / "cdn-watch-history.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "time": int(self.clock()),
            "service": outcome.service_id,
            "host": outcome.host,
            "phase": phase,
            "sustained_mbps": round(outcome.sustained_mbps, 2),
            "average_mbps": round(outcome.average_mbps, 2),
            "peak_mbps": round(outcome.peak_mbps, 2),
            "cdn": outcome.cdn,
            "resolver": resolver,
            "policy": outcome.policy,
        }
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        try:
            lines = path.read_text().splitlines()
            if len(lines) > MAX_HISTORY_LINES:
                path.write_text("\n".join(lines[-MAX_HISTORY_LINES:]) + "\n")
                path.chmod(0o600)
        except OSError:
            pass

    def _save_service_state(self, service_id: str, values: dict[str, Any]) -> None:
        state = self.state_store.load()
        services = state.setdefault("services", {})
        info = services.setdefault(service_id, {})
        now = int(self.clock())
        changed = any(info.get(key) != value for key, value in values.items())
        last_heartbeat = _safe_int(state.get("daemon_heartbeat"))
        if not changed and now - last_heartbeat < HEARTBEAT_WRITE_SECONDS:
            return
        info.update(values)
        info["updated_at"] = now
        state["daemon_heartbeat"] = now
        self.state_store.save(state)

    def _attempt_autofix(self, outcome: HealthOutcome, spec: ServiceSpec, cdn: str) -> tuple[bool, str, str]:
        fix = spec.autofix
        if not fix.enabled:
            return False, "", "automatic repair disabled"
        if not is_direct_policy(outcome.policy):
            return False, "", "current route is not DIRECT"
        if outcome.host not in fix.dns_overrides:
            return False, "", "host is not in verified DNS allowlist"
        if cdn not in fix.trigger_cdns:
            return False, "", f"CDN {cdn} is not an allowlisted repair trigger"
        if not self.config.mac_profile:
            return False, "", "primary Surge profile is not configured"
        result = self.editor.ensure(
            Path(self.config.mac_profile),
            {outcome.host: fix.dns_overrides[outcome.host]},
            reload_profile=fix.reload,
        )
        return result.ok, result.backup_path, result.message

    def handle_outcome(self, outcome: HealthOutcome) -> None:
        state = self.state_store.load()
        prior = state.get("services", {}).get(outcome.service_id, {})
        phase = str(prior.get("phase") or "idle")
        spec = self.specs[outcome.service_id]
        now_float = self.clock()
        now = int(now_float)

        if phase == "awaiting_restart":
            if outcome.status in {"idle", "observing"}:
                self._remind_restart_if_needed(outcome, prior, now_float)
                self._save_service_state(outcome.service_id, {"phase": phase, "status": outcome.status})
                return
            repair_at = _safe_float(prior.get("repair_at"))
            if outcome.newest_start_date <= repair_at:
                self._remind_restart_if_needed(outcome, prior, now_float)
                self._save_service_state(outcome.service_id, {"phase": phase, "status": outcome.status})
                return
            cdn, resolver = self._dns_context(outcome.host, outcome.cdn)
            expected = str(prior.get("expected_cdn") or spec.autofix.expected_cdn)
            cdn_matches = not expected or cdn == expected
            if outcome.status in {"healthy", "usable"} and cdn_matches:
                quality = "健康" if outcome.status == "healthy" else "可用"
                self._notify_or_escalate(
                    outcome,
                    f"✅ {outcome.service_name}自动修复已通过复验\n新连接已切换到预期 CDN，持续速度约 {outcome.sustained_mbps:.1f} Mbps，状态{quality}。",
                    "repair verified",
                )
                self._record_history(outcome, "repair_verified", resolver)
                self._save_service_state(outcome.service_id, {
                    "phase": "healthy",
                    "status": outcome.status,
                    "last_mbps": round(outcome.sustained_mbps, 2),
                    "cdn": cdn,
                    "host": outcome.host,
                    "verified_connection_started_at": outcome.newest_start_date,
                    "backup_path": "",
                    "repair_detail": "",
                })
                return
            if outcome.status not in {"degraded", "critical", "healthy", "usable"}:
                return
            if not cdn_matches:
                failure = f"new connection used CDN {cdn}, expected {expected}"
            else:
                failure = f"new connection remained {outcome.status} at {outcome.sustained_mbps:.1f} Mbps"
            backup = str(prior.get("backup_path") or "")
            if backup and spec.autofix.rollback_on_failure and self.config.mac_profile:
                rolled_back = self.editor.restore(
                    Path(self.config.mac_profile), Path(backup), reload_profile=spec.autofix.reload,
                )
                reason = f"{failure}; {rolled_back.message}"
            else:
                reason = failure
            notified = self._notify_or_escalate(
                outcome,
                f"❌ {outcome.service_name}自动修复未通过复验\n已停止继续自动改动，正在升级分析。",
                reason,
            )
            if notified:
                self._write_pending(outcome, reason)
            self._record_history(outcome, "repair_failed", resolver)
            self._save_service_state(outcome.service_id, {
                "phase": "failed",
                "status": outcome.status,
                "diagnostic": reason,
                "backup_path": "",
            })
            return

        if outcome.status in {"idle", "observing"}:
            self._save_service_state(outcome.service_id, {
                "phase": phase if phase in {"repairing", "awaiting_restart"} else outcome.status,
                "status": outcome.status,
            })
            return

        if outcome.status in {"healthy", "usable"}:
            if phase in {"suspect", "diagnosing", "repairing", "awaiting_restart", "failed", "needs_analysis"}:
                quality = "健康" if outcome.status == "healthy" else "可用"
                message = (
                    f"✅ {outcome.service_name}线路已恢复\n"
                    f"当前持续速度约 {outcome.sustained_mbps:.1f} Mbps，状态{quality}，可以继续播放。"
                )
                self._notify_or_escalate(outcome, message, "recovery notification")
                self._record_history(outcome, "recovered")
            self._save_service_state(outcome.service_id, {
                "phase": "healthy",
                "status": outcome.status,
                "last_mbps": round(outcome.sustained_mbps, 2),
                "cdn": outcome.cdn,
                "host": outcome.host,
            })
            return

        if outcome.status not in {"degraded", "critical"}:
            return
        last_opened = int(prior.get("incident_opened_at", 0) or 0)
        if (
            last_opened
            and phase not in {"suspect", "diagnosing", "repairing", "awaiting_restart"}
            and now - last_opened < spec.cooldown_seconds
        ):
            return

        cdn, resolver = self._dns_context(outcome.host, outcome.cdn)
        if phase not in {"suspect", "diagnosing", "repairing", "awaiting_restart"}:
            message = (
                f"⚠️ 检测到{outcome.service_name}播放线路异常\n"
                f"真实媒体速度持续约 {outcome.sustained_mbps:.1f} Mbps，正在后台排查 DNS、CDN 和直连线路。"
            )
            self._notify_or_escalate(outcome, message, "incident opened")
            self._record_history(outcome, "suspect", resolver)
            self._save_service_state(outcome.service_id, {
                "phase": "diagnosing",
                "status": outcome.status,
                "incident_opened_at": now,
                "pre_fix_mbps": round(outcome.sustained_mbps, 2),
                "host": outcome.host,
                "cdn": cdn,
                "resolver": resolver,
            })
            phase = "diagnosing"

        fixed, backup, detail = self._attempt_autofix(outcome, spec, cdn)
        if fixed:
            message = (
                f"🔧 {outcome.service_name}线路已执行精确 DNS/CDN 纠错\n"
                "Surge缓存已刷新。请退出 Apple TV App 后重新打开播放，后台会继续复验。"
            )
            self._notify_or_escalate(outcome, message, "repair applied")
            self._record_history(outcome, "repair_applied", resolver)
            self._save_service_state(outcome.service_id, {
                "phase": "awaiting_restart",
                "status": outcome.status,
                "repair_at": now_float,
                "backup_path": backup,
                "repair_detail": detail,
                "expected_cdn": spec.autofix.expected_cdn,
                "restart_reminded_at": 0,
            })
            return

        self._write_pending(outcome, detail)
        self._record_history(outcome, "needs_analysis", resolver)
        self._save_service_state(outcome.service_id, {
            "phase": "needs_analysis",
            "status": outcome.status,
            "diagnostic": detail,
        })

    def run(self, *, stop_after_seconds: float = 0) -> int:
        started = self.clock()

        def stop(_signum: int, _frame: Any) -> None:
            self.running = False

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        self._save_service_state("_daemon", {
            "phase": "running",
            "pid": os.getpid(),
            "signature": self.signature,
        })
        try:
            for event in self.client.watch_request_updates(
                poll_interval=self.settings.poll_interval_seconds,
                idle_interval=max(10.0, self.settings.poll_interval_seconds * 5),
                is_target=self._is_target_event,
                should_stop=lambda: (
                    not self.running
                    or bool(stop_after_seconds and self.clock() - started >= stop_after_seconds)
                ),
            ):
                now = self.clock()
                if stop_after_seconds and now - started >= stop_after_seconds:
                    break
                if not self.running:
                    break
                if "_tick" in event:
                    for tracker in self.trackers.values():
                        try:
                            self.handle_outcome(tracker.evaluate(now))
                        except Exception:
                            self.event_errors += 1
                    if now - self.last_health_persist_at >= HEARTBEAT_WRITE_SECONDS:
                        last_request_at = _safe_float(event.get("_last_request_at"))
                        poll_ok = bool(event.get("_poll_ok"))
                        controller_at = _safe_float(event.get("_controller_at"))
                        self._save_service_state("_daemon", {
                            "phase": "running",
                            "pid": os.getpid(),
                            "signature": self.signature,
                            "watch_state": "connected" if poll_ok else "unavailable",
                            "last_request_at": int(last_request_at),
                            "controller_at": int(controller_at),
                            "controller_latency_ms": round(_safe_float(event.get("_controller_latency_ms")), 1),
                            "event_errors": self.event_errors,
                        })
                        self.last_health_persist_at = now
                    continue
                for tracker in self.trackers.values():
                    try:
                        if tracker.ingest(event, now):
                            break
                    except Exception:
                        self.event_errors += 1
        finally:
            state = self.state_store.load()
            state["daemon_heartbeat"] = int(self.clock())
            state["daemon_stopped_at"] = int(self.clock())
            self.state_store.save(state)
        return 0


def pid_path(config: SentryConfig) -> Path:
    return config.state_dir / "cdn-watch.pid"


def read_pid(config: SentryConfig) -> int:
    try:
        return int(pid_path(config).read_text().strip())
    except Exception:
        return 0


def process_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def process_is_watcher(pid: int) -> bool:
    if not process_alive(pid):
        return False
    try:
        result = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except Exception:
        return False
    command = result.stdout.strip()
    return "surge_sentry.cli cdn-watch run" in command


def watch_signature(config: SentryConfig) -> str:
    digest = hashlib.sha256()
    for path in (
        config.root / "surge_sentry" / "cdn_watch.py",
        config.root / "surge_sentry" / "surge.py",
        config.cdn_watch_config,
    ):
        try:
            digest.update(path.read_bytes())
        except OSError:
            digest.update(str(path).encode("utf-8"))
    return digest.hexdigest()[:16]


def ensure_daemon(config: SentryConfig) -> tuple[bool, str]:
    if not config.cdn_watch_enabled:
        return True, "disabled"
    if not config.cdn_watch_config.exists():
        return False, "config missing"
    path = pid_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = config.state_dir / "cdn-watch.ensure.lock"
    if lock_path.exists() and time.time() - lock_path.stat().st_mtime > 30:
        lock_path.unlink(missing_ok=True)
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        time.sleep(0.5)
        return (process_is_watcher(read_pid(config)), "running" if process_is_watcher(read_pid(config)) else "start in progress")
    try:
        os.write(lock_fd, str(os.getpid()).encode("ascii"))
        os.close(lock_fd)
        existing = read_pid(config)
        if process_is_watcher(existing):
            state = StateStore(config.state_dir / "cdn-watch-state.json").load()
            daemon_state = state.get("services", {}).get("_daemon", {})
            active_signature = str(daemon_state.get("signature") or "")
            heartbeat = _safe_int(state.get("daemon_heartbeat"))
            controller_at = _safe_int(daemon_state.get("controller_at"))
            now = int(time.time())
            signature_matches = active_signature == watch_signature(config)
            heartbeat_fresh = bool(heartbeat and now - heartbeat <= WATCH_STALE_SECONDS)
            controller_fresh = bool(controller_at and now - controller_at <= WATCH_STALE_SECONDS)
            if signature_matches and heartbeat_fresh and controller_fresh:
                return True, "running"
            stopped, detail = stop_daemon(config)
            if not stopped:
                return False, f"stale watcher could not stop: {detail}"
        path.unlink(missing_ok=True)
        log_dir = config.state_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "cdn-watch.log"
        if log_path.exists() and log_path.stat().st_size > 2 * MB:
            archived = log_path.with_suffix(".log.1")
            archived.unlink(missing_ok=True)
            log_path.replace(archived)
            archived.chmod(0o600)
        log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.fchmod(log_fd, 0o600)
        with os.fdopen(log_fd, "ab") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "surge_sentry.cli", "cdn-watch", "run"],
                cwd=config.root,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        path.write_text(str(proc.pid) + "\n")
        path.chmod(0o600)
        time.sleep(0.4)
        return (proc.poll() is None, "started" if proc.poll() is None else "start failed")
    finally:
        lock_path.unlink(missing_ok=True)


def stop_daemon(config: SentryConfig) -> tuple[bool, str]:
    pid = read_pid(config)
    if not process_is_watcher(pid):
        pid_path(config).unlink(missing_ok=True)
        return True, "not running"
    os.kill(pid, signal.SIGTERM)
    for _ in range(130):
        if not process_alive(pid):
            pid_path(config).unlink(missing_ok=True)
            return True, "stopped"
        time.sleep(0.1)
    return False, "stop timeout"


def _trim_event_archive(path: Path, limit: int = MAX_PROCESSED_EVENTS) -> None:
    if not path.exists():
        return
    files = sorted(path.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for item in files[limit:]:
        item.unlink(missing_ok=True)


def _quarantine_pending(config: SentryConfig, path: Path) -> None:
    if path.is_symlink():
        path.unlink(missing_ok=True)
        return
    quarantine_dir = config.state_dir / "cdn-watch-quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.chmod(0o700)
    target = quarantine_dir / f"{int(time.time() * 1000)}-{path.name}"
    try:
        path.replace(target)
        target.chmod(0o600)
    except OSError:
        path.unlink(missing_ok=True)


def _valid_pending(path: Path, data: dict[str, Any]) -> bool:
    event_id = str(data.get("event_id") or "")
    return bool(
        re.fullmatch(r"[a-zA-Z0-9_-]{8,160}", event_id)
        and path.stem == event_id
        and data.get("service")
        and data.get("reason")
    )


def consume_pending(config: SentryConfig, limit: int = 5) -> list[dict[str, Any]]:
    pending_dir = config.state_dir / "cdn-watch-pending"
    inflight_dir = config.state_dir / "cdn-watch-inflight"
    pending_dir.mkdir(parents=True, exist_ok=True)
    inflight_dir.mkdir(parents=True, exist_ok=True)
    pending_dir.chmod(0o700)
    inflight_dir.chmod(0o700)
    items: list[dict[str, Any]] = []
    for path in sorted(pending_dir.glob("*.json"))[:limit]:
        target = inflight_dir / path.name
        try:
            path.replace(target)
        except OSError:
            continue
        data = StateStore(target).load()
        if not _valid_pending(target, data):
            _quarantine_pending(config, target)
            continue
        items.append(data)
    if len(items) < limit:
        cutoff = time.time() - PENDING_RETRY_SECONDS
        seen_ids = {str(item.get("event_id") or "") for item in items}
        for path in sorted(inflight_dir.glob("*.json")):
            if len(items) >= limit or path.stat().st_mtime > cutoff:
                continue
            data = StateStore(path).load()
            if not _valid_pending(path, data):
                _quarantine_pending(config, path)
                continue
            event_id = str(data.get("event_id") or "")
            if event_id not in seen_ids:
                items.append(data)
                seen_ids.add(event_id)
    return items


def ack_pending(config: SentryConfig, event_id: str) -> tuple[bool, str]:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,160}", event_id):
        return False, "invalid event id"
    inflight = config.state_dir / "cdn-watch-inflight" / f"{event_id}.json"
    if not inflight.is_file() or inflight.is_symlink():
        return False, "event not found"
    data = StateStore(inflight).load()
    if not _valid_pending(inflight, data):
        _quarantine_pending(config, inflight)
        return False, "invalid event quarantined"
    processed_dir = config.state_dir / "cdn-watch-processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.chmod(0o700)
    target = processed_dir / inflight.name
    inflight.replace(target)
    target.chmod(0o600)
    _trim_event_archive(processed_dir)
    return True, "acknowledged"


def resolve_pending(
    config: SentryConfig,
    event_id: str,
    message: str,
    *,
    target: str = "telegram",
    notifier: HermesNotifier | None = None,
) -> tuple[bool, str]:
    inflight = config.state_dir / "cdn-watch-inflight" / f"{event_id}.json"
    data = StateStore(inflight).load() if inflight.is_file() and not inflight.is_symlink() else {}
    if not _valid_pending(inflight, data):
        return False, "event not found or invalid"
    text = str(message or "").strip()
    if not text or len(text) > 4000:
        return False, "message must contain 1-4000 characters"
    sender = notifier or HermesNotifier(target)
    if not sender.send(text):
        return False, "delivery failed; event retained for retry"
    return ack_pending(config, event_id)
