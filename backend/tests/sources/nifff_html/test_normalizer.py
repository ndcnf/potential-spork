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


def test_normalize_parsed_films_warns_when_screening_end_is_inferred() -> None:
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

    assert bundle.warnings == [
        "Inferred screening end from film duration: film=a-useful-ghost starts_at=2025-07-05T19:00:00+02:00"
    ]


def test_normalize_parsed_films_classifies_packages_and_members() -> None:
    package_start = datetime.fromisoformat("2025-07-05T16:45:00+02:00")
    package = ParsedFilm(
        title="Asian Shorts",
        slug="asian-shorts",
        source_url="https://nifff.ch/prog/2025/film-package/asian-shorts",
        cycle_name="Shorts Programs",
        duration_minutes=92,
        screenings=[
            ParsedScreening(
                starts_at=package_start,
                ends_at=None,
                venue_name="Rex",
            )
        ],
    )
    package_member = ParsedFilm(
        title="Atom & Void",
        slug="atom-void",
        source_url="https://nifff.ch/prog/2025/film/atom-void",
        cycle_name="Shorts Programs",
        duration_minutes=9,
    )
    standalone = ParsedFilm(
        title="A Useful Ghost",
        slug="a-useful-ghost",
        source_url="https://nifff.ch/prog/2025/film/a-useful-ghost",
        cycle_name="International Competition",
        duration_minutes=130,
        screenings=[
            ParsedScreening(
                starts_at=datetime.fromisoformat("2025-07-05T19:00:00+02:00"),
                ends_at=None,
                venue_name="Arcades",
            )
        ],
    )

    bundle = normalize_parsed_films(parsed_films=[package, package_member, standalone], year=2025)

    planning_type_by_slug = {film.slug: film.planning_type for film in bundle.films}
    assert planning_type_by_slug == {
        "asian-shorts": "package",
        "atom-void": "package_member",
        "a-useful-ghost": "standalone",
    }
