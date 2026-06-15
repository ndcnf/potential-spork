from __future__ import annotations

from datetime import timedelta, datetime

from app.sources.nifff_html.normalizer import normalize_parsed_films
from app.sources.nifff_html.parser import ParsedFilm, ParsedScreening


def test_normalize_parsed_films_includes_venues_and_screenings() -> None:
    parsed_film = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
        screenings=[
            ParsedScreening(
                starts_at=datetime.fromisoformat("2025-07-05T18:00:00+02:00"),
                ends_at=datetime.fromisoformat("2025-07-05T20:26:00+02:00"),
                venue_name="Théâtre",
                ticket_url="https://nifff.ch/tickets/1",
                source_url="https://nifff.ch/screenings/1",
            )
        ],
    )

    bundle = normalize_parsed_films(parsed_films=[parsed_film], year=2025)

    assert len(bundle.venues) == 1
    assert bundle.venues[0].source_key == "nifff:venue:theatre"
    assert len(bundle.screenings) == 1
    assert bundle.screenings[0].film_source_key == "nifff:film:a-cure-for-wellness"
    assert bundle.screenings[0].venue_source_key == "nifff:venue:theatre"


def test_normalize_parsed_films_deduplicates_venues_across_screenings() -> None:
    parsed_film = ParsedFilm(
        title="A Useful Ghost",
        slug="a-useful-ghost",
        source_url="https://nifff.ch/prog/2025/film/a-useful-ghost",
        screenings=[
            ParsedScreening(
                starts_at=datetime.fromisoformat("2025-07-05T19:00:00+02:00"),
                ends_at=None,
                venue_name="Arcades",
            ),
            ParsedScreening(
                starts_at=datetime.fromisoformat("2025-07-08T16:30:00+02:00"),
                ends_at=None,
                venue_name="Arcades",
            ),
        ],
    )

    bundle = normalize_parsed_films(parsed_films=[parsed_film], year=2025)

    assert len(bundle.venues) == 1
    assert len(bundle.screenings) == 2


def test_normalize_parsed_films_infers_screening_end_from_film_duration() -> None:
    starts_at = datetime.fromisoformat("2025-07-05T19:00:00+02:00")
    parsed_film = ParsedFilm(
        title="A Useful Ghost",
        slug="a-useful-ghost",
        source_url="https://nifff.ch/prog/2025/film/a-useful-ghost",
        duration_minutes=130,
        screenings=[
            ParsedScreening(
                starts_at=starts_at,
                ends_at=None,
                venue_name="Arcades",
            )
        ],
    )

    bundle = normalize_parsed_films(parsed_films=[parsed_film], year=2025)

    assert bundle.screenings[0].ends_at == starts_at + timedelta(minutes=130)
