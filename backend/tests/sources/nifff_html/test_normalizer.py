from __future__ import annotations

from datetime import datetime

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
