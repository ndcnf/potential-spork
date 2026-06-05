from __future__ import annotations

from app.repositories.venues import VenueRepository
from app.schemas.imported import ImportedVenue


def test_venue_repository_creates_venue_when_missing(db_session) -> None:
    repository = VenueRepository(db_session)

    result = repository.upsert(ImportedVenue(source_key="nifff:venue:theatre", name="Théâtre"))

    assert result.created is True
    assert result.venue.id is not None
    assert result.venue.source_key == "nifff:venue:theatre"


def test_venue_repository_backfills_source_key_from_legacy_name(db_session, venue_factory) -> None:
    existing = venue_factory(name="Théâtre", source_key=None)
    repository = VenueRepository(db_session)

    result = repository.upsert(ImportedVenue(source_key="nifff:venue:theatre", name="Théâtre"))

    assert result.created is False
    assert result.venue.id == existing.id
    assert result.venue.source_key == "nifff:venue:theatre"
