"""
Utilitaires de temps.
"""
from datetime import datetime, time, timedelta
from typing import Optional


def get_utc_now() -> datetime:
    return datetime.utcnow()


def is_between_times(check_time: time, start_time: time, end_time: time) -> bool:
    if start_time <= end_time:
        return start_time <= check_time <= end_time
    return check_time >= start_time or check_time <= end_time


def time_until(target: time, from_time: Optional[datetime] = None) -> timedelta:
    dt = from_time or datetime.utcnow()
    target_dt = datetime.combine(dt.date(), target)
    if target_dt <= dt:
        target_dt += timedelta(days=1)
    return target_dt - dt


def format_duration(td: timedelta) -> str:
    seconds = int(td.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{minutes}min"