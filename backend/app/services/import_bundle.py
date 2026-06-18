from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.screening import Screening
from app.repositories.cycles import CycleRepository
from app.repositories.films import FilmRepository
from app.repositories.screenings import ScreeningRepository
from app.repositories.venues import VenueRepository
from app.schemas.imported import CanonicalImportBundle, ImportReport


logger = logging.getLogger(__name__)


def apply_import_bundle(*, db: Session, bundle: CanonicalImportBundle, report: ImportReport) -> ImportReport:
    cycle_repository = CycleRepository(db)
    film_repository = FilmRepository(db)
    venue_repository = VenueRepository(db)
    screening_repository = ScreeningRepository(db)

    cycles_by_source_key = {}
    for imported_cycle in bundle.cycles:
        result = cycle_repository.upsert(imported_cycle)
        if result.created:
            report.cycles_created += 1
        else:
            report.cycles_updated += 1
        cycles_by_source_key[imported_cycle.source_key] = result.cycle

    films_by_source_key = {}
    for imported_film in bundle.films:
        cycle = None
        if imported_film.cycle_source_key:
            cycle = cycles_by_source_key.get(imported_film.cycle_source_key)

        result = film_repository.upsert(imported_film, cycle=cycle)
        if result.created:
            report.films_created += 1
        else:
            report.films_updated += 1
        films_by_source_key[imported_film.source_key] = result.film

    venues_by_source_key = {}
    for imported_venue in bundle.venues:
        result = venue_repository.upsert(imported_venue)
        if result.created:
            report.venues_created += 1
        else:
            report.venues_updated += 1
        venues_by_source_key[imported_venue.source_key] = result.venue

    incoming_screening_source_keys = {screening.source_key for screening in bundle.screenings}
    for imported_screening in bundle.screenings:
        film = films_by_source_key.get(imported_screening.film_source_key)
        if film is None:
            warning_message = "Skipping screening import because film source key is unknown"
            report.warnings.append(
                f"{warning_message}: screening={imported_screening.source_key} film={imported_screening.film_source_key}"
            )
            logger.warning(
                warning_message,
                extra={
                    "screening_source_key": imported_screening.source_key,
                    "film_source_key": imported_screening.film_source_key,
                },
            )
            continue

        venue = None
        if imported_screening.venue_source_key:
            venue = venues_by_source_key.get(imported_screening.venue_source_key)

        result = screening_repository.upsert(imported_screening, film=film, venue=venue)
        if result.created:
            report.screenings_created += 1
        else:
            report.screenings_updated += 1

    imported_film_ids = [film.id for film in films_by_source_key.values()]
    if imported_film_ids:
        stale_screenings = db.scalars(
            select(Screening).where(
                Screening.film_id.in_(imported_film_ids),
                Screening.source_key.is_not(None),
                Screening.source_key.not_in(incoming_screening_source_keys),
            )
        ).all()
        for stale_screening in stale_screenings:
            db.delete(stale_screening)
            report.screenings_pruned += 1
        if stale_screenings:
            db.flush()

    return report
