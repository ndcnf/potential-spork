from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.models.screening import Screening
from app.models.venue import Venue
from app.schemas.imported import ImportedScreening


@dataclass(slots=True)
class UpsertScreeningResult:
    screening: Screening
    created: bool


class ScreeningRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(
        self,
        imported_screening: ImportedScreening,
        *,
        film: Film,
        venue: Venue | None = None,
    ) -> UpsertScreeningResult:
        screening = self._db.scalar(select(Screening).where(Screening.source_key == imported_screening.source_key))
        created = screening is None

        if screening is None:
            screening = Screening(
                source_key=imported_screening.source_key,
                film_id=film.id,
                venue_id=venue.id if venue else None,
                starts_at=imported_screening.starts_at,
                ends_at=imported_screening.ends_at,
                source_url=imported_screening.source_url,
            )

        screening.source_key = imported_screening.source_key
        screening.film_id = film.id
        screening.venue_id = venue.id if venue else None
        screening.starts_at = imported_screening.starts_at
        screening.ends_at = imported_screening.ends_at
        screening.source_url = imported_screening.source_url

        self._db.add(screening)
        self._db.flush()
        return UpsertScreeningResult(screening=screening, created=created)
