from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RoutingContract:
    name: str
    target: str
    required_sources: tuple[str, ...]
    required_rules: tuple[str, ...]


def load_contracts(path: Path) -> list[RoutingContract]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text())
    entries = data.get("contracts", []) if isinstance(data, dict) else []
    contracts: list[RoutingContract] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        target = str(entry.get("target") or "").strip()
        if not name or not target:
            continue
        contracts.append(RoutingContract(
            name=name,
            target=target,
            required_sources=tuple(str(item) for item in entry.get("required_sources", []) if str(item).strip()),
            required_rules=tuple(str(item) for item in entry.get("required_rules", []) if str(item).strip()),
        ))
    return contracts


def audit_profile(profile: Path, contracts: list[RoutingContract]) -> list[str]:
    if not profile.is_file():
        return [f"路由契约审计无法读取 profile：{profile}"]
    rules = [line.strip() for line in profile.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    findings: list[str] = []
    for contract in contracts:
        for source in contract.required_sources:
            matches = [line for line in rules if source in line]
            if not matches:
                findings.append(f"{contract.name} 缺少规则源 {source}")
                continue
            if not any(_policy(line) == contract.target for line in matches):
                findings.append(f"{contract.name} 的 {source} 未指向 {contract.target}")
        for rule in contract.required_rules:
            if rule not in rules:
                findings.append(f"{contract.name} 缺少精确规则 {rule}")
    return findings


def _policy(line: str) -> str:
    parts = [part.strip().strip('"') for part in line.split(",")]
    return parts[2] if len(parts) >= 3 else ""
