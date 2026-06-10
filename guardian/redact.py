from __future__ import annotations

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

PATTERNS = [
    ("github_token", re.compile(r"gh[oprsu]_[A-Za-z0-9_]{20,}")),
    ("url_with_secret", re.compile(r"https?://[^\s'\"`]*(token|password|passwd|secret|key)=[^\s'\"`]+", re.I)),
    ("subscription_url", re.compile(r"https?://[^\s'\"`]*(sub|subscribe|subscription)[^\s'\"`]*", re.I)),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("real_ip", re.compile(r"\b(?!(?:127|0|10|172\.(?:1[6-9]|2\d|3[0-1])|192\.168|203\.0\.113|198\.51\.100|192\.0\.2)\.)\d{1,3}(?:\.\d{1,3}){3}\b")),
    ("home_path_user", re.compile(r"/Users/[A-Za-z0-9_.-]+")),
    ("known_private_label", re.compile(r"\b(Rex|behoss|Bwg|Mac mini|telegram:\d+)\b", re.I)),
]


def redact_text(text: str) -> str:
    redacted = text
    for kind, pattern in PATTERNS:
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
            for kind, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(path.relative_to(root), idx, kind, line.strip()[:240]))
    return findings
