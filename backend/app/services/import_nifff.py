from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.schemas.imports import ImportSummary
from app.services.import_catalog import import_catalog
from app.sources.nifff_html.source import NifffHtmlSource


logger = logging.getLogger(__name__)


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/archives/{year}/schedule?type=film"
    )
    bundle, report = import_catalog(source=source, year=year)
    cycles_created = 0
    films_created = 0
    films_updated = 0

    cycles_by_source_key: dict[str, Cycle] = {}
    for imported_cycle in bundle.cycles:
        cycle = db.scalar(select(Cycle).where(Cycle.slug == imported_cycle.slug))
        if cycle is None:
            cycle = Cycle(name=imported_cycle.name, slug=imported_cycle.slug)
            db.add(cycle)
            db.flush()
            cycles_created += 1
        cycles_by_source_key[imported_cycle.source_key] = cycle

    for imported_film in bundle.films:
        cycle = None
        if imported_film.cycle_source_key:
            cycle = cycles_by_source_key.get(imported_film.cycle_source_key)

        film = db.scalar(select(Film).where(Film.slug == imported_film.slug))
        if film is None:
            film = Film(title=imported_film.title, slug=imported_film.slug, priority="medium")
            films_created += 1
        else:
            films_updated += 1

        film.title = imported_film.title
        film.directors = imported_film.directors
        film.year = imported_film.year
        film.countries = imported_film.countries
        film.duration_minutes = imported_film.duration_minutes
        film.tagline = imported_film.tagline
        film.premiere_label = imported_film.premiere_label
        film.short_description = imported_film.short_description
        film.cast = imported_film.cast
        film.synopsis = imported_film.synopsis
        film.language = imported_film.language
        film.age_rating = imported_film.age_rating
        film.poster_url = imported_film.poster_url
        film.source_url = imported_film.source_url
        film.cycle_id = cycle.id if cycle else None

        db.add(film)

    db.commit()
    if report.warnings:
        logger.info("Import completed with warnings", extra={"warnings": report.warnings, "year": year})
    return ImportSummary(cycles_created=cycles_created, films_created=films_created, films_updated=films_updated)
