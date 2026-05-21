from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event


FESTIVAL_TIMEZONE = ZoneInfo("Europe/Zurich")


def ensure_local_datetime(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(FESTIVAL_TIMEZONE)
    return value.replace(tzinfo=FESTIVAL_TIMEZONE)


def build_calendar(screenings: list) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Potential Spork//Festival Planner//FR")
    calendar.add("version", "2.0")

    for screening in screenings:
        if screening.starts_at is None:
            continue

        starts_at = ensure_local_datetime(screening.starts_at)
        if starts_at is None:
            continue
        ends_at = ensure_local_datetime(screening.ends_at) or (starts_at + timedelta(minutes=screening.film.duration_minutes or 120))

        event = Event()
        event.add("uid", f"screening-{screening.id}@potential-spork")
        event.add("dtstamp", datetime.now(timezone.utc))
        event.add("summary", screening.film.title)
        event.add("dtstart", starts_at)
        event.add("dtend", ends_at)
        if screening.venue is not None:
            event.add("location", screening.venue.name)
        event.add("description", screening.film.tagline or "")
        calendar.add_component(event)

    return calendar.to_ical()
