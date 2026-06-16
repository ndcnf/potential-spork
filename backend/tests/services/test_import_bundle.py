from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.models.screening import Screening
from app.models.venue import Venue
from app.schemas.imported import CanonicalImportBundle, ImportReport, ImportedCycle, ImportedFilm, ImportedScreening, ImportedVenue
from app.services.import_bundle import apply_import_bundle


def test_apply_import_bundle_persists_catalog_entities_and_updates_report(db_session: Session) -> None:
    bundle = CanonicalImportBundle(
        source_name="test_source",
        year=2025,
        cycles=[
            ImportedCycle(
                source_key="test:cycle:international-competition",
                name="International Competition",
                slug="international-competition",
            )
        ],
        films=[
            ImportedFilm(
                source_key="test:film:a-cure-for-wellness",
                title="A Cure for Wellness",
                slug="a-cure-for-wellness",
                source_url="https://example.test/film/a-cure-for-wellness",
                cycle_source_key="test:cycle:international-competition",
            )
        ],
        venues=[ImportedVenue(source_key="test:venue:theatre", name="Theatre")],
        screenings=[
            ImportedScreening(
                source_key="test:screening:a-cure-theatre",
                film_source_key="test:film:a-cure-for-wellness",
                venue_source_key="test:venue:theatre",
                starts_at=None,
                ends_at=None,
                source_url="https://example.test/screening/a-cure-theatre",
            )
        ],
    )
    report = ImportReport(source_name="test_source", year=2025)

    apply_import_bundle(db=db_session, bundle=bundle, report=report)

    film = db_session.scalar(select(Film).where(Film.source_key == "test:film:a-cure-for-wellness"))
    venue = db_session.scalar(select(Venue).where(Venue.source_key == "test:venue:theatre"))
    screening = db_session.scalar(select(Screening).where(Screening.source_key == "test:screening:a-cure-theatre"))

    assert report.cycles_created == 1
    assert report.films_created == 1
    assert report.venues_created == 1
    assert report.screenings_created == 1
    assert film is not None
    assert venue is not None
    assert screening is not None
    assert screening.film_id == film.id
    assert screening.venue_id == venue.id


def test_apply_import_bundle_warns_when_screening_references_unknown_film(
    db_session: Session,
    caplog,
) -> None:
    bundle = CanonicalImportBundle(
        source_name="test_source",
        year=2025,
        screenings=[
            ImportedScreening(
                source_key="test:screening:unknown-film",
                film_source_key="test:film:missing",
                venue_source_key=None,
                starts_at=None,
                ends_at=None,
            )
        ],
    )
    report = ImportReport(source_name="test_source", year=2025)

    with caplog.at_level("WARNING"):
        apply_import_bundle(db=db_session, bundle=bundle, report=report)

    assert any("Skipping screening import because film source key is unknown" in message for message in caplog.messages)
    assert report.warnings == [
        "Skipping screening import because film source key is unknown: screening=test:screening:unknown-film film=test:film:missing"
    ]
