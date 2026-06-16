from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.film import Film
from app.schemas.imports import ImportSummary
from app.services.import_bundle import apply_import_bundle
from app.services.import_catalog import import_catalog
from app.sources.nifff_html.normalizer import category_tokens
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


def _is_package_url(source_url: str | None) -> bool:
    return source_url is not None and "/film-package/" in source_url


def _sync_existing_package_member_planning_types(db: Session) -> None:
    films = db.query(Film).options(joinedload(Film.cycle), selectinload(Film.screenings)).all()
    package_cycle_tokens = set().union(
        *(
            category_tokens(film.cycle.name if film.cycle else None)
            for film in films
            if film.planning_type == "package" or _is_package_url(film.source_url)
        )
    )

    if not package_cycle_tokens:
        return

    for film in films:
        if film.planning_type == "package" or _is_package_url(film.source_url):
            film.planning_type = "package"
            continue

        if not film.screenings and category_tokens(film.cycle.name if film.cycle else None).intersection(package_cycle_tokens):
            film.planning_type = "package_member"
            continue

        if film.planning_type == "package_member":
            film.planning_type = "standalone"


def _import_nifff_from_source(db: Session, source: _SourceWithMode, year: int) -> ImportSummary:
    bundle, report = import_catalog(source=source, year=year)
    apply_import_bundle(db=db, bundle=bundle, report=report)
    _sync_existing_package_member_planning_types(db)

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
    source = NifffHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_archive(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffArchiveHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffArchiveHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_live(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffLiveHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffLiveHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)
