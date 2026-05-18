from datetime import timedelta

from icalendar import Calendar, Event


def build_calendar(screenings: list) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Potential Spork//Festival Planner//FR")
    calendar.add("version", "2.0")

    for screening in screenings:
        if screening.starts_at is None:
            continue

        event = Event()
        event.add("summary", screening.film.title)
        event.add("dtstart", screening.starts_at)
        event.add("dtend", screening.ends_at or (screening.starts_at + timedelta(minutes=screening.film.duration_minutes or 120)))
        if screening.venue is not None:
            event.add("location", screening.venue.name)
        event.add("description", screening.film.tagline or "")
        calendar.add_component(event)

    return calendar.to_ical()
