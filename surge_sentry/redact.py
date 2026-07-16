from __future__ import annotations

import os
import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "state", "logs"}
SKIP_FILES = {".env", "redact.py"}
SKIP_SUFFIXES = {
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".tar",
    ".ttf",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}

BASE_PATTERNS = [
    ("github_token", re.compile(r"gh[oprsu]_[A-Za-z0-9_]{20,}")),
    ("url_with_secret", re.compile(r"https?://[^\s'\"`]*(token|password|passwd|secret|key)=[^\s'\"`]+", re.I)),
    ("subscription_url", re.compile(r"https?://[^\s'\"`]*(sub|subscribe|subscription)[^\s'\"`]*", re.I)),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("real_ip", re.compile(r"\b(?!(?:127|0|10|172\.(?:1[6-9]|2\d|3[0-1])|192\.168|203\.0\.113|198\.51\.100|192\.0\.2)\.)\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("home_path_user", re.compile(r"/Users/[A-Za-z0-9_.-]+")),
]

PUBLIC_INFRA_NETWORKS = tuple(ipaddress.ip_network(value) for value in (
    "1.1.1.1/32",
    "8.8.8.8/32",
    "8.8.4.4/32",
    "17.0.0.0/8",
    "146.75.0.0/16",
    "151.101.0.0/16",
    "199.232.0.0/16",
    "223.5.5.5/32",
))


def is_public_infrastructure_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(address in network for network in PUBLIC_INFRA_NETWORKS)


def patterns() -> list[tuple[str, re.Pattern[str]]]:
    values = [item.strip() for item in os.environ.get("SURGE_SENTRY_REDACT_WORDS", "").split(",") if item.strip()]
    if not values:
        return BASE_PATTERNS
    extra = "|".join(re.escape(item) for item in values)
    return [*BASE_PATTERNS, ("local_private_label", re.compile(rf"\b({extra})\b", re.I))]


def redact_text(text: str) -> str:
    redacted = text
    for kind, pattern in patterns():
        redacted = pattern.sub(f"[redacted:{kind}]", redacted)
    return redacted


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str
    text: str


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & SKIP_DIRS:
            continue
        if path.name in SKIP_FILES:
            continue
        if path.name.endswith((".local.env", ".local.json")):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def scan(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            for kind, pattern in patterns():
                if kind == "real_ip":
                    matches = [item.group(0) for item in pattern.finditer(line)]
                    matched = any(not is_public_infrastructure_ip(item) for item in matches)
                else:
                    matched = bool(pattern.search(line))
                if matched:
                    findings.append(Finding(path.relative_to(root), idx, kind, line.strip()[:240]))
    return findings
