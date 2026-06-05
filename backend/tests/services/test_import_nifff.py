from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.models.screening import Screening
from app.models.venue import Venue
from app.schemas.imported import CanonicalImportBundle, ImportReport, ImportedCycle, ImportedFilm, ImportedScreening, ImportedVenue
from app.services.import_nifff import import_nifff_catalog


def build_bundle(*, short_description: str | None, tagline: str = "Psychological horror") -> CanonicalImportBundle:
    return CanonicalImportBundle(
        source_name="nifff_html",
        year=2025,
        cycles=[
            ImportedCycle(
                source_key="nifff:cycle:international-competition",
                name="International Competition",
                slug="international-competition",
            )
        ],
        films=[
            ImportedFilm(
                source_key="nifff:film:a-cure-for-wellness",
                title="A Cure for Wellness",
                slug="a-cure-for-wellness",
                source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
                cycle_source_key="nifff:cycle:international-competition",
                directors="Gore Verbinski",
                year=2016,
                countries="DE/LU/US",
                duration_minutes=146,
                tagline=tagline,
                short_description=short_description,
                poster_url="https://nifff.ch/images/cure.jpg",
            )
        ],
    )


def fake_report() -> ImportReport:
    return ImportReport(source_name="nifff_html", year=2025)


def test_import_nifff_catalog_creates_cycles_and_films(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.import_nifff.import_catalog",
        lambda source, year: (build_bundle(short_description="A young executive discovers a terrifying secret."), fake_report()),
    )

    result = import_nifff_catalog(db=db_session, year=2025)

    cycle = db_session.scalar(select(Cycle).where(Cycle.slug == "international-competition"))
    film = db_session.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))

    assert result.cycles_created == 1
    assert result.films_created == 1
    assert result.films_updated == 0
    assert cycle is not None
    assert film is not None
    assert film.cycle_id == cycle.id
    assert film.poster_url == "https://nifff.ch/images/cure.jpg"
    assert film.source_key == "nifff:film:a-cure-for-wellness"


def test_import_nifff_catalog_is_idempotent_for_existing_film(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.import_nifff.import_catalog",
        lambda source, year: (build_bundle(short_description="A young executive discovers a terrifying secret."), fake_report()),
    )

    first = import_nifff_catalog(db=db_session, year=2025)
    second = import_nifff_catalog(db=db_session, year=2025)

    films = db_session.scalars(select(Film)).all()
    cycles = db_session.scalars(select(Cycle)).all()

    assert first.films_created == 1
    assert second.films_created == 0
    assert second.films_updated == 1
    assert len(films) == 1
    assert len(cycles) == 1


def test_import_nifff_catalog_updates_existing_film_fields(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.import_nifff.import_catalog",
        lambda source, year: (build_bundle(short_description="A young executive discovers a terrifying secret."), fake_report()),
    )
    import_nifff_catalog(db=db_session, year=2025)

    monkeypatch.setattr(
        "app.services.import_nifff.import_catalog",
        lambda source, year: (build_bundle(short_description="Updated description.", tagline="Updated genre"), fake_report()),
    )
    result = import_nifff_catalog(db=db_session, year=2025)

    film = db_session.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))

    assert result.films_updated == 1
    assert film is not None
    assert film.tagline == "Updated genre"
    assert film.short_description == "Updated description."


def test_import_nifff_catalog_persists_venues_and_screenings_from_bundle(db_session: Session, monkeypatch) -> None:
    bundle = build_bundle(short_description="A young executive discovers a terrifying secret.")
    bundle.venues.append(ImportedVenue(source_key="nifff:venue:theatre", name="Théâtre"))
    bundle.screenings.append(
        ImportedScreening(
            source_key="nifff:screening:a-cure-theatre-2025-07-05t1800",
            film_source_key="nifff:film:a-cure-for-wellness",
            venue_source_key="nifff:venue:theatre",
            starts_at=None,
            ends_at=None,
            source_url="https://nifff.ch/screening/1",
        )
    )
    monkeypatch.setattr("app.services.import_nifff.import_catalog", lambda source, year: (bundle, fake_report()))

    result = import_nifff_catalog(db=db_session, year=2025)
    film = db_session.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))
    venue = db_session.scalar(select(Venue).where(Venue.source_key == "nifff:venue:theatre"))
    screening = db_session.scalar(
        select(Screening).where(Screening.source_key == "nifff:screening:a-cure-theatre-2025-07-05t1800")
    )

    assert result.films_created == 1
    assert film is not None
    assert venue is not None
    assert screening is not None
    assert screening.film_id == film.id
    assert screening.venue_id == venue.id
    assert screening.source_url == "https://nifff.ch/screening/1"


def test_import_nifff_catalog_logs_warning_when_screening_film_is_unknown(
    db_session: Session,
    monkeypatch,
    caplog,
) -> None:
    bundle = CanonicalImportBundle(
        source_name="nifff_html",
        year=2025,
        screenings=[
            ImportedScreening(
                source_key="nifff:screening:unknown-film",
                film_source_key="nifff:film:missing",
                venue_source_key=None,
                starts_at=None,
                ends_at=None,
                source_url=None,
            )
        ],
    )
    monkeypatch.setattr("app.services.import_nifff.import_catalog", lambda source, year: (bundle, fake_report()))

    with caplog.at_level("WARNING"):
        import_nifff_catalog(db=db_session, year=2025)

    assert any("Skipping screening import because film source key is unknown" in message for message in caplog.messages)


def test_import_nifff_catalog_skips_invalid_cards(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.import_nifff.import_catalog",
        lambda source, year: (CanonicalImportBundle(source_name="nifff_html", year=2025), fake_report()),
    )

    result = import_nifff_catalog(db=db_session, year=2025)

    assert result.cycles_created == 0
    assert result.films_created == 0
    assert db_session.scalars(select(Film)).all() == []
