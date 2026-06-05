from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy.orm import Session

from app.repositories.cycles import CycleRepository
from app.repositories.films import FilmRepository
from app.repositories.screenings import ScreeningRepository
from app.repositories.venues import VenueRepository
from app.schemas.imports import ImportSummary
from app.services.import_catalog import import_catalog
from app.sources.nifff_html.source import NifffArchiveHtmlSource, NifffHtmlSource, NifffLiveHtmlSource


logger = logging.getLogger(__name__)


class _SourceWithMode(Protocol):
    source_mode: str


def _summary_from_report(report: object) -> ImportSummary:
    return ImportSummary(
        cycles_created=report.cycles_created,
        films_created=report.films_created,
        films_updated=report.films_updated,
        venues_created=report.venues_created,
        venues_updated=report.venues_updated,
        screenings_created=report.screenings_created,
        screenings_updated=report.screenings_updated,
        warnings_count=len(report.warnings),
        errors_count=len(report.errors),
    )


def _import_nifff_from_source(db: Session, source: _SourceWithMode, year: int) -> ImportSummary:
    bundle, report = import_catalog(source=source, year=year)
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

    db.commit()
    logger.info(
        "Import completed",
        extra={
            "year": year,
            "source_name": report.source_name,
            "source_mode": source.source_mode,
            "cycles_created": report.cycles_created,
            "cycles_updated": report.cycles_updated,
            "films_created": report.films_created,
            "films_updated": report.films_updated,
            "venues_created": report.venues_created,
            "venues_updated": report.venues_updated,
            "screenings_created": report.screenings_created,
            "screenings_updated": report.screenings_updated,
            "warnings": report.warnings,
            "errors": report.errors,
        },
    )
    return _summary_from_report(report)


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/archives/{year}/schedule?type=film"
    )
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_archive(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffArchiveHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/archives/{year}/schedule?type=film"
    )
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_live(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffLiveHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/programme/?type=film"
    )
    return _import_nifff_from_source(db=db, source=source, year=year)
