from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.screenings import ScreeningRepository
from app.schemas.imported import ImportedScreening


def test_screening_repository_creates_screening_when_missing(db_session, film_factory, venue_factory) -> None:
    repository = ScreeningRepository(db_session)
    film = film_factory(source_key="nifff:film:a-cure-for-wellness")
    venue = venue_factory(source_key="nifff:venue:theatre")

    result = repository.upsert(
        ImportedScreening(
            source_key="nifff:screening:a-cure-theatre-2030-07-05t1800",
            film_source_key="nifff:film:a-cure-for-wellness",
            venue_source_key="nifff:venue:theatre",
            starts_at=datetime(2030, 7, 5, 18, 0, tzinfo=UTC),
            ends_at=datetime(2030, 7, 5, 20, 0, tzinfo=UTC),
            source_url="https://nifff.ch/screening/1",
        ),
        film=film,
        venue=venue,
    )

    assert result.created is True
    assert result.screening.source_key == "nifff:screening:a-cure-theatre-2030-07-05t1800"
    assert result.screening.film_id == film.id
    assert result.screening.venue_id == venue.id


def test_screening_repository_updates_existing_screening(db_session, screening_factory, film_factory) -> None:
    film = film_factory(source_key="nifff:film:a-cure-for-wellness")
    existing = screening_factory(
        film=film,
        source_key="nifff:screening:a-cure-theatre-2030-07-05t1800",
        source_url=None,
    )
    repository = ScreeningRepository(db_session)

    result = repository.upsert(
        ImportedScreening(
            source_key="nifff:screening:a-cure-theatre-2030-07-05t1800",
            film_source_key="nifff:film:a-cure-for-wellness",
            venue_source_key=None,
            starts_at=datetime(2030, 7, 5, 18, 0, tzinfo=UTC),
            ends_at=datetime(2030, 7, 5, 20, 0, tzinfo=UTC),
            source_url="https://nifff.ch/screening/1",
        ),
        film=film,
        venue=None,
    )

    assert result.created is False
    assert result.screening.id == existing.id
    assert result.screening.source_url == "https://nifff.ch/screening/1"
