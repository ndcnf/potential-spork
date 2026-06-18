from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.models.screening import Screening
from app.models.cycle import Cycle
from app.models.venue import Venue
from app.schemas.imported import CanonicalImportBundle, ImportReport, ImportedCycle, ImportedFilm, ImportedScreening, ImportedVenue
from app.services.import_bundle import apply_import_bundle, prune_stale_catalog_entities


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


def test_apply_import_bundle_updates_corrected_screening_source_key_without_losing_choice(
    db_session: Session,
) -> None:
    initial_bundle = CanonicalImportBundle(
        source_name="nifff_html",
        year=2025,
        films=[
            ImportedFilm(
                source_key="nifff:film:clown-in-a-cornfield",
                title="Clown in a Cornfield",
                slug="clown-in-a-cornfield",
                source_url="https://nifff.ch/prog/2025/film/clown-in-a-cornfield",
                cycle_source_key=None,
            )
        ],
        venues=[ImportedVenue(source_key="nifff:venue:open-air", name="Open Air")],
        screenings=[
            ImportedScreening(
                source_key="nifff:screening:clown-in-a-cornfield:open-air:2025-07-04T00:45:00",
                film_source_key="nifff:film:clown-in-a-cornfield",
                venue_source_key="nifff:venue:open-air",
                starts_at=datetime(2025, 7, 4, 0, 45),
                ends_at=datetime(2025, 7, 4, 2, 22),
                source_url="https://nifff.ch/prog/2025/film/clown-in-a-cornfield",
            )
        ],
    )
    apply_import_bundle(db=db_session, bundle=initial_bundle, report=ImportReport(source_name="nifff_html", year=2025))
    existing = db_session.scalar(select(Screening))
    assert existing is not None
    existing.selection_status = "tentative"
    db_session.commit()

    corrected_bundle = CanonicalImportBundle(
        source_name="nifff_html",
        year=2025,
        films=initial_bundle.films,
        venues=initial_bundle.venues,
        screenings=[
            ImportedScreening(
                source_key="nifff:screening:clown-in-a-cornfield:open-air:2025-07-05T00:45:00",
                film_source_key="nifff:film:clown-in-a-cornfield",
                venue_source_key="nifff:venue:open-air",
                starts_at=datetime(2025, 7, 5, 0, 45),
                ends_at=datetime(2025, 7, 5, 2, 22),
                source_url="https://nifff.ch/prog/2025/film/clown-in-a-cornfield",
            )
        ],
    )
    report = ImportReport(source_name="nifff_html", year=2025)

    apply_import_bundle(db=db_session, bundle=corrected_bundle, report=report)

    screenings = db_session.scalars(select(Screening)).all()

    assert len(screenings) == 1
    assert screenings[0].source_key == "nifff:screening:clown-in-a-cornfield:open-air:2025-07-05T00:45:00"
    assert screenings[0].starts_at == datetime(2025, 7, 5, 0, 45)
    assert screenings[0].selection_status == "tentative"
    assert report.screenings_updated == 1


def test_apply_import_bundle_prunes_stale_screenings_for_imported_films(
    db_session: Session,
) -> None:
    bundle = CanonicalImportBundle(
        source_name="nifff_html",
        year=2025,
        films=[
            ImportedFilm(
                source_key="nifff:film:clown-in-a-cornfield",
                title="Clown in a Cornfield",
                slug="clown-in-a-cornfield",
                source_url="https://nifff.ch/prog/2025/film/clown-in-a-cornfield",
                cycle_source_key=None,
            )
        ],
        venues=[ImportedVenue(source_key="nifff:venue:open-air", name="Open Air")],
        screenings=[
            ImportedScreening(
                source_key="nifff:screening:clown-in-a-cornfield:open-air:2025-07-05T00:45:00",
                film_source_key="nifff:film:clown-in-a-cornfield",
                venue_source_key="nifff:venue:open-air",
                starts_at=datetime(2025, 7, 5, 0, 45),
                ends_at=datetime(2025, 7, 5, 2, 22),
            )
        ],
    )
    apply_import_bundle(db=db_session, bundle=bundle, report=ImportReport(source_name="nifff_html", year=2025))
    film = db_session.scalar(select(Film).where(Film.source_key == "nifff:film:clown-in-a-cornfield"))
    assert film is not None
    db_session.add(
        Screening(
            source_key="nifff:screening:clown-in-a-cornfield:open-air:obsolete",
            film_id=film.id,
            starts_at=datetime(2025, 7, 4, 0, 45),
            ends_at=datetime(2025, 7, 4, 2, 22),
        )
    )
    db_session.commit()

    report = ImportReport(source_name="nifff_html", year=2025)

    apply_import_bundle(db=db_session, bundle=bundle, report=report)

    screenings = db_session.scalars(select(Screening)).all()

    assert len(screenings) == 1
    assert screenings[0].source_key == "nifff:screening:clown-in-a-cornfield:open-air:2025-07-05T00:45:00"
    assert report.screenings_pruned == 1


def test_apply_import_bundle_prunes_stale_nifff_catalog_entities(
    db_session: Session,
) -> None:
    stale_cycle = Cycle(source_key="nifff:cycle:old-cycle", name="Old Cycle", slug="old-cycle")
    stale_venue = Venue(source_key="nifff:venue:old-venue", name="Old Venue")
    stale_film = Film(
        source_key="nifff:film:old-film",
        title="Old Film",
        slug="old-film",
        priority="high",
        cycle=stale_cycle,
    )
    db_session.add_all([stale_cycle, stale_venue, stale_film])
    db_session.flush()
    db_session.add(
        Screening(
            source_key="nifff:screening:old-film:old-venue:2025-07-05T18:00:00",
            film_id=stale_film.id,
            venue_id=stale_venue.id,
            starts_at=datetime(2025, 7, 5, 18, 0),
            ends_at=datetime(2025, 7, 5, 20, 0),
            selection_status="confirmed",
        )
    )
    db_session.commit()

    bundle = CanonicalImportBundle(
        source_name="nifff_html",
        year=2026,
        cycles=[ImportedCycle(source_key="nifff:cycle:new-cycle", name="New Cycle", slug="new-cycle")],
        films=[
            ImportedFilm(
                source_key="nifff:film:new-film",
                title="New Film",
                slug="new-film",
                source_url="https://nifff.ch/prog/2026/film/new-film",
                cycle_source_key="nifff:cycle:new-cycle",
            )
        ],
        venues=[ImportedVenue(source_key="nifff:venue:new-venue", name="New Venue")],
        screenings=[
            ImportedScreening(
                source_key="nifff:screening:new-film:new-venue:2026-07-05T18:00:00",
                film_source_key="nifff:film:new-film",
                venue_source_key="nifff:venue:new-venue",
                starts_at=datetime(2026, 7, 5, 18, 0),
                ends_at=datetime(2026, 7, 5, 20, 0),
            )
        ],
    )

    report = ImportReport(source_name="nifff_html", year=2026)
    apply_import_bundle(db=db_session, bundle=bundle, report=report)
    prune_stale_catalog_entities(db=db_session, bundle=bundle, report=report)

    assert db_session.scalar(select(Film).where(Film.source_key == "nifff:film:old-film")) is None
    assert db_session.scalar(select(Screening).where(Screening.source_key.like("nifff:screening:old-film:%"))) is None
    assert db_session.scalar(select(Cycle).where(Cycle.source_key == "nifff:cycle:old-cycle")) is None
    assert db_session.scalar(select(Venue).where(Venue.source_key == "nifff:venue:old-venue")) is None
    assert db_session.scalar(select(Film).where(Film.source_key == "nifff:film:new-film")) is not None
