from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.imports import ImportSummary
from app.services.import_pipeline import run_import_pipeline
from app.services.import_postprocessing import sync_existing_package_member_planning_types
from app.sources.base import FestivalSource
from app.sources.nifff_html.source import NifffArchiveHtmlSource, NifffHtmlSource, NifffLiveHtmlSource


def _import_nifff_from_source(db: Session, source: FestivalSource, year: int) -> ImportSummary:
    return run_import_pipeline(
        db=db,
        source=source,
        year=year,
        postprocessors=(sync_existing_package_member_planning_types,),
    )


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_archive(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffArchiveHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffArchiveHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)


def import_nifff_catalog_from_live(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    source = NifffLiveHtmlSource(schedule_url_template=schedule_url) if schedule_url else NifffLiveHtmlSource()
    return _import_nifff_from_source(db=db, source=source, year=year)
