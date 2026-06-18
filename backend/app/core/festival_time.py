from __future__ import annotations

from datetime import datetime, timedelta


FESTIVAL_DAY_CUTOFF_HOUR = 6


def real_datetime_from_festival_day(*, year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    value = datetime(year=year, month=month, day=day, hour=hour, minute=minute)
    if hour < FESTIVAL_DAY_CUTOFF_HOUR:
        return value + timedelta(days=1)
    return value


def festival_day_key(value: datetime) -> str:
    display_date = value
    if value.hour < FESTIVAL_DAY_CUTOFF_HOUR:
        display_date = value - timedelta(days=1)
    return display_date.date().isoformat()
