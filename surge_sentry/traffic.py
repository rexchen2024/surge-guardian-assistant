from __future__ import annotations

import calendar
import datetime as dt
import fnmatch
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


BYTES_PER_GB = 1024 ** 3


@dataclass(frozen=True)
class TrafficRecord:
    host: str
    path: str
    policy: str
    total_gb: float
    down_gb: float
    up_gb: float
    requests: int


@dataclass(frozen=True)
class TrafficRisk:
    severity: str
    message: str
    current_gb: float
    budget_gb: float
    top_records: list[TrafficRecord]


def record_key(record: TrafficRecord) -> str:
    return "\x1f".join([record.host, record.path, record.policy])


def latest_session_db(base_dir: Path, local_time: time.struct_time | None = None) -> Path | None:
    session_dir = base_dir / "Session"
    if not session_dir.exists():
        return None
    current = local_time or time.localtime()
    today = time.strftime("%Y%m%d", current)
    today_db = session_dir / f"{today}.sqlite"
    if today_db.exists():
        return today_db
    files = sorted(session_dir.glob("*.sqlite"), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def current_month_db(base_dir: Path, local_time: time.struct_time | None = None) -> Path | None:
    monthly_dir = base_dir / "Monthly"
    current = local_time or time.localtime()
    path = monthly_dir / f"{time.strftime('%Y%m', current)}.sqlite"
    return path if path.exists() else None


def _matches_any(value: str, patterns: list[str]) -> bool:
    text = value.lower()
    return any(fnmatch.fnmatch(text, pattern.lower()) for pattern in patterns)


def _policy_where(patterns: list[str]) -> tuple[str, list[str]]:
    if not patterns:
        return "1=0", []
    parts = ["lower(coalesce(ZPOLICY,'')) like lower(?)" for _ in patterns]
    return "(" + " or ".join(parts) + ")", patterns


def read_policy_records(db_path: Path, policy_patterns: list[str], limit: int = 100) -> list[TrafficRecord]:
    if not db_path.exists() or not policy_patterns:
        return []
    where, params = _policy_where(policy_patterns)
    sql = f"""
        select coalesce(ZHOST,'') as host,
               coalesce(ZPATH,'') as path,
               coalesce(ZPOLICY,'') as policy,
               sum(coalesce(ZTOTAL,0)) as total,
               sum(coalesce(ZDOWN,0)) as down,
               sum(coalesce(ZUP,0)) as up,
               sum(coalesce(ZREQUESTCOUNT,0)) as requests
        from ZSGTRAFFICSTATRECORD
        where {where}
        group by ZHOST, ZPATH, ZPOLICY
        order by total desc
        limit ?
    """
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(sql, [*params, int(limit)]).fetchall()
    records: list[TrafficRecord] = []
    for host, path, policy, total, down, up, requests in rows:
        records.append(TrafficRecord(
            host=str(host or ""),
            path=str(path or ""),
            policy=str(policy or ""),
            total_gb=float(total or 0) / BYTES_PER_GB,
            down_gb=float(down or 0) / BYTES_PER_GB,
            up_gb=float(up or 0) / BYTES_PER_GB,
            requests=int(requests or 0),
        ))
    return records


def total_gb(records: list[TrafficRecord]) -> float:
    return sum(item.total_gb for item in records)


def records_to_snapshot(records: list[TrafficRecord]) -> dict[str, dict[str, object]]:
    return {
        record_key(item): {
            "host": item.host,
            "path": item.path,
            "policy": item.policy,
            "total_gb": item.total_gb,
            "down_gb": item.down_gb,
            "up_gb": item.up_gb,
            "requests": item.requests,
        }
        for item in records
    }


def diff_records(records: list[TrafficRecord], baseline: dict[str, dict[str, object]]) -> list[TrafficRecord]:
    deltas: list[TrafficRecord] = []
    for item in records:
        prior = baseline.get(record_key(item), {})
        total_delta = max(0.0, item.total_gb - float(prior.get("total_gb", 0) or 0))
        down_delta = max(0.0, item.down_gb - float(prior.get("down_gb", 0) or 0))
        up_delta = max(0.0, item.up_gb - float(prior.get("up_gb", 0) or 0))
        requests_delta = max(0, item.requests - int(prior.get("requests", 0) or 0))
        if total_delta <= 0 and requests_delta <= 0:
            continue
        deltas.append(TrafficRecord(
            host=item.host,
            path=item.path,
            policy=item.policy,
            total_gb=total_delta,
            down_gb=down_delta,
            up_gb=up_delta,
            requests=requests_delta,
        ))
    return sorted(deltas, key=lambda record: record.total_gb, reverse=True)


def budget_day(reset_day: int, local_time: time.struct_time | None = None) -> tuple[int, int]:
    current = local_time or time.localtime()
    today = dt.date(current.tm_year, current.tm_mon, current.tm_mday)

    def cycle_date(year: int, month: int) -> dt.date:
        day = max(1, min(int(reset_day or 1), calendar.monthrange(year, month)[1]))
        return dt.date(year, month, day)

    def add_month(year: int, month: int, delta: int) -> tuple[int, int]:
        index = year * 12 + month - 1 + delta
        return index // 12, index % 12 + 1

    current_start = cycle_date(today.year, today.month)
    if today >= current_start:
        start = current_start
        next_year, next_month = add_month(today.year, today.month, 1)
        end = cycle_date(next_year, next_month)
    else:
        prev_year, prev_month = add_month(today.year, today.month, -1)
        start = cycle_date(prev_year, prev_month)
        end = current_start
    elapsed = (today - start).days + 1
    total = (end - start).days
    return max(1, elapsed), max(1, total)


def format_top_records(records: list[TrafficRecord], limit: int = 5) -> str:
    parts = []
    for item in records[:limit]:
        host = item.host or item.path or "(unknown)"
        policy = f" via {item.policy}" if item.policy else ""
        parts.append(f"{host} {item.total_gb:.1f}GB{policy}")
    return "; ".join(parts)


def find_direct_leak_records(
    records: list[TrafficRecord],
    host_patterns: list[str],
    min_gb: float,
) -> list[TrafficRecord]:
    if not host_patterns:
        return []
    return [
        item for item in records
        if item.total_gb >= min_gb and _matches_any(item.host, host_patterns)
    ]


def analyze_traffic(
    session_records: list[TrafficRecord],
    monthly_records: list[TrafficRecord],
    *,
    monthly_cap_gb: float,
    reset_day: int,
    daily_warn_ratio: float,
    daily_critical_ratio: float,
    direct_host_patterns: list[str],
    direct_leak_min_gb: float,
    local_time: time.struct_time | None = None,
) -> list[TrafficRisk]:
    risks: list[TrafficRisk] = []
    if monthly_cap_gb <= 0:
        return risks

    elapsed, total_days = budget_day(reset_day, local_time)
    daily_budget = monthly_cap_gb / total_days
    today_gb = total_gb(session_records)
    if today_gb >= daily_budget * daily_critical_ratio:
        severity = "high"
    elif today_gb >= daily_budget * daily_warn_ratio:
        severity = "medium"
    else:
        severity = ""
    if severity:
        risks.append(TrafficRisk(
            severity,
            f"今天被监控代理策略流量 {today_gb:.1f}GB，超过当前账期第 {elapsed}/{total_days} 天的保守日预算 {daily_budget:.1f}GB。",
            today_gb,
            daily_budget,
            session_records[:8],
        ))

    direct_leaks = find_direct_leak_records(session_records, direct_host_patterns, direct_leak_min_gb)
    if direct_leaks:
        risks.append(TrafficRisk(
            "high",
            "命中直连优先媒体模式的流量正在使用被监控代理策略。",
            total_gb(direct_leaks),
            direct_leak_min_gb,
            direct_leaks[:8],
        ))
    elif monthly_records:
        monthly_leaks = find_direct_leak_records(monthly_records, direct_host_patterns, max(direct_leak_min_gb * 3, 5.0))
        if monthly_leaks:
            risks.append(TrafficRisk(
                "medium",
                "月度历史显示命中直连优先媒体模式的流量近期使用过被监控代理策略。",
                total_gb(monthly_leaks),
                max(direct_leak_min_gb * 3, 5.0),
                monthly_leaks[:8],
            ))
    return risks
