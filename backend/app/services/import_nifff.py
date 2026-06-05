from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.repositories.cycles import CycleRepository
from app.repositories.films import FilmRepository
from app.repositories.screenings import ScreeningRepository
from app.repositories.venues import VenueRepository
from app.schemas.imports import ImportSummary
from app.services.import_catalog import import_catalog
from app.sources.nifff_html.source import NifffHtmlSource


logger = logging.getLogger(__name__)


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/archives/{year}/schedule?type=film"
    )
    bundle, report = import_catalog(source=source, year=year)
    cycle_repository = CycleRepository(db)
    film_repository = FilmRepository(db)
    venue_repository = VenueRepository(db)
    screening_repository = ScreeningRepository(db)
    cycles_created = 0
    films_created = 0
    films_updated = 0

    cycles_by_source_key = {}
    for imported_cycle in bundle.cycles:
        result = cycle_repository.upsert(imported_cycle)
        if result.created:
            cycles_created += 1
        cycles_by_source_key[imported_cycle.source_key] = result.cycle

    films_by_source_key = {}
    for imported_film in bundle.films:
        cycle = None
        if imported_film.cycle_source_key:
            cycle = cycles_by_source_key.get(imported_film.cycle_source_key)

        result = film_repository.upsert(imported_film, cycle=cycle)
        if result.created:
            films_created += 1
        else:
            films_updated += 1
        films_by_source_key[imported_film.source_key] = result.film

    venues_by_source_key = {}
    for imported_venue in bundle.venues:
        result = venue_repository.upsert(imported_venue)
        venues_by_source_key[imported_venue.source_key] = result.venue

    for imported_screening in bundle.screenings:
        film = films_by_source_key.get(imported_screening.film_source_key)
        if film is None:
            logger.warning(
                "Skipping screening import because film source key is unknown",
                extra={"screening_source_key": imported_screening.source_key, "film_source_key": imported_screening.film_source_key},
            )
            continue

        venue = None
        if imported_screening.venue_source_key:
            venue = venues_by_source_key.get(imported_screening.venue_source_key)

        screening_repository.upsert(imported_screening, film=film, venue=venue)

    db.commit()
    if report.warnings:
        logger.info("Import completed with warnings", extra={"warnings": report.warnings, "year": year})
    return ImportSummary(cycles_created=cycles_created, films_created=films_created, films_updated=films_updated)
