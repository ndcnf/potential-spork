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


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffHtmlSource(
        schedule_url_template=schedule_url or "https://nifff.ch/archives/{year}/schedule?type=film"
    )
    return _import_nifff_from_source(db=db, source=source, year=year)
