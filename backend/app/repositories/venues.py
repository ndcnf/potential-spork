from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.venue import Venue
from app.schemas.imported import ImportedVenue


@dataclass(slots=True)
class UpsertVenueResult:
    venue: Venue
    created: bool


class VenueRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(self, imported_venue: ImportedVenue) -> UpsertVenueResult:
        venue = self._db.scalar(select(Venue).where(Venue.source_key == imported_venue.source_key))
        if venue is None:
            venue = self._db.scalar(select(Venue).where(Venue.name == imported_venue.name))
        created = venue is None

        if venue is None:
            venue = Venue(source_key=imported_venue.source_key, name=imported_venue.name)
        else:
            venue.source_key = imported_venue.source_key
            venue.name = imported_venue.name

        self._db.add(venue)
        self._db.flush()
        return UpsertVenueResult(venue=venue, created=created)
