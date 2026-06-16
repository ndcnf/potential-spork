from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.schemas.imported import ImportReport
from app.schemas.imports import ImportSummary
from app.services.import_bundle import apply_import_bundle
from app.services.import_catalog import import_catalog
from app.sources.base import FestivalSource


logger = logging.getLogger(__name__)

ImportPostprocessor = Callable[[Session], None]


def summary_from_report(report: ImportReport) -> ImportSummary:
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


def run_import_pipeline(
    *,
    db: Session,
    source: FestivalSource,
    year: int,
    postprocessors: tuple[ImportPostprocessor, ...] = (),
) -> ImportSummary:
    bundle, report = import_catalog(source=source, year=year)
    apply_import_bundle(db=db, bundle=bundle, report=report)
    for postprocessor in postprocessors:
        postprocessor(db)

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
    return summary_from_report(report)
