from datetime import datetime, timedelta, timezone
from collections.abc import Iterable
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event


FESTIVAL_TIMEZONE = ZoneInfo("Europe/Zurich")


def ensure_local_datetime(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(FESTIVAL_TIMEZONE)
    return value.replace(tzinfo=FESTIVAL_TIMEZONE)


def row_value(screening, key: str, default=None):
    if isinstance(screening, dict):
        return screening.get(key, default)
    return getattr(screening, key, default)


def build_calendar(screenings: Iterable) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Potential Spork//Festival Planner//FR")
    calendar.add("version", "2.0")

    for screening in screenings:
        starts_at_value = row_value(screening, "starts_at")
        if starts_at_value is None:
            continue

        starts_at = ensure_local_datetime(starts_at_value)
        if starts_at is None:
            continue
        ends_at = ensure_local_datetime(row_value(screening, "ends_at")) or (starts_at + timedelta(minutes=row_value(screening, "film_duration_minutes", 120) or 120))

        event = Event()
        event.add("uid", f"screening-{row_value(screening, 'id')}@potential-spork")
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("summary", row_value(screening, "film_title", "Projection"))
        event.add("dtstart", starts_at)
        event.add("dtend", ends_at)
        venue_name = row_value(screening, "venue_name")
        if venue_name:
            event.add("location", venue_name)
        event.add("description", row_value(screening, "film_tagline", "") or "")
        calendar.add_component(event)

    return calendar.to_ical()
