from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from icalendar import Calendar

from app.services.export_ics import FESTIVAL_TIMEZONE, build_calendar, ensure_local_datetime, row_value


def test_build_calendar_creates_event_for_valid_screening() -> None:
    screening = {
        "id": 1,
        "starts_at": datetime(2030, 7, 5, 18, 0, tzinfo=UTC),
        "ends_at": datetime(2030, 7, 5, 20, 0, tzinfo=UTC),
        "film_title": "A Cure for Wellness",
        "film_tagline": "Mind-bending wellness horror",
        "film_duration_minutes": 120,
        "venue_name": "Théâtre",
    }

    calendar_bytes = build_calendar([screening])
    calendar = Calendar.from_ical(calendar_bytes)
    events = [component for component in calendar.walk() if component.name == "VEVENT"]

    assert len(events) == 1
    assert str(events[0].get("summary")) == "A Cure for Wellness"
    assert str(events[0].get("location")) == "Théâtre"


def test_build_calendar_skips_screening_without_start() -> None:
    screening = {"id": 1, "starts_at": None, "film_title": "Missing Start"}

    calendar = Calendar.from_ical(build_calendar([screening]))
    events = [component for component in calendar.walk() if component.name == "VEVENT"]

    assert events == []


def test_build_calendar_uses_duration_fallback_when_end_missing() -> None:
    screening = {
        "id": 1,
        "starts_at": datetime(2030, 7, 5, 18, 0, tzinfo=UTC),
        "ends_at": None,
        "film_title": "Fallback Duration",
        "film_duration_minutes": 90,
    }

    calendar = Calendar.from_ical(build_calendar([screening]))
    event = next(component for component in calendar.walk() if component.name == "VEVENT")

    assert event.decoded("dtend") == datetime(2030, 7, 5, 21, 30, tzinfo=FESTIVAL_TIMEZONE)


def test_build_calendar_keeps_real_late_night_datetime() -> None:
    screening = {
        "id": 1,
        "starts_at": datetime(2030, 7, 6, 1, 0, tzinfo=FESTIVAL_TIMEZONE),
        "ends_at": datetime(2030, 7, 6, 2, 30, tzinfo=FESTIVAL_TIMEZONE),
        "film_title": "Late Night Screening",
        "film_duration_minutes": 90,
    }

    calendar = Calendar.from_ical(build_calendar([screening]))
    event = next(component for component in calendar.walk() if component.name == "VEVENT")

    assert event.decoded("dtstart") == datetime(2030, 7, 6, 1, 0, tzinfo=FESTIVAL_TIMEZONE)
    assert event.decoded("dtend") == datetime(2030, 7, 6, 2, 30, tzinfo=FESTIVAL_TIMEZONE)


def test_build_calendar_uses_default_duration_when_missing_everywhere() -> None:
    screening = {
        "id": 1,
        "starts_at": datetime(2030, 7, 5, 18, 0, tzinfo=UTC),
        "ends_at": None,
        "film_title": "Default Duration",
        "film_duration_minutes": None,
    }

    calendar = Calendar.from_ical(build_calendar([screening]))
    event = next(component for component in calendar.walk() if component.name == "VEVENT")

    assert event.decoded("dtend") == datetime(2030, 7, 5, 22, 0, tzinfo=FESTIVAL_TIMEZONE)


def test_ensure_local_datetime_converts_aware_datetime_to_festival_timezone() -> None:
    value = datetime(2030, 7, 5, 18, 0, tzinfo=UTC)

    assert ensure_local_datetime(value).tzinfo == FESTIVAL_TIMEZONE


def test_row_value_supports_mapping_and_object_inputs() -> None:
    mapping = {"film_title": "Mapped"}
    obj = SimpleNamespace(film_title="Object")

    assert row_value(mapping, "film_title") == "Mapped"
    assert row_value(obj, "film_title") == "Object"
