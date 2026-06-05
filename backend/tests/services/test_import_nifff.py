from __future__ import annotations

from types import SimpleNamespace

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.services.import_nifff import import_nifff_catalog


def test_import_nifff_catalog_creates_cycles_and_films(db_session: Session, fixture_text_loader, monkeypatch) -> None:
    listing_html = fixture_text_loader("nifff_html/listing_nominal.html")
    detail_html = fixture_text_loader("nifff_html/detail_nominal.html")

    monkeypatch.setattr("app.services.import_nifff.build_session", lambda: SimpleNamespace())

    def fake_fetch_html(_session: object, url: str) -> str:
        if "schedule" in url:
            return listing_html
        return detail_html

    monkeypatch.setattr("app.services.import_nifff.fetch_html", fake_fetch_html)

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


def test_import_nifff_catalog_is_idempotent_for_existing_film(db_session: Session, fixture_text_loader, monkeypatch) -> None:
    listing_html = fixture_text_loader("nifff_html/listing_nominal.html")
    detail_html = fixture_text_loader("nifff_html/detail_nominal.html")

    monkeypatch.setattr("app.services.import_nifff.build_session", lambda: SimpleNamespace())
    monkeypatch.setattr(
        "app.services.import_nifff.fetch_html",
        lambda _session, url: listing_html if "schedule" in url else detail_html,
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


def test_import_nifff_catalog_updates_existing_film_fields(db_session: Session, fixture_text_loader, monkeypatch) -> None:
    listing_html = fixture_text_loader("nifff_html/listing_nominal.html")
    detail_html = fixture_text_loader("nifff_html/detail_nominal.html")
    updated_detail_html = detail_html.replace("Psychological horror", "Updated genre").replace(
        "A young executive discovers a terrifying secret.",
        "Updated description.",
    )

    monkeypatch.setattr("app.services.import_nifff.build_session", lambda: SimpleNamespace())
    monkeypatch.setattr(
        "app.services.import_nifff.fetch_html",
        lambda _session, url: listing_html if "schedule" in url else detail_html,
    )
    import_nifff_catalog(db=db_session, year=2025)

    monkeypatch.setattr(
        "app.services.import_nifff.fetch_html",
        lambda _session, url: listing_html if "schedule" in url else updated_detail_html,
    )
    result = import_nifff_catalog(db=db_session, year=2025)

    film = db_session.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))

    assert result.films_updated == 1
    assert film is not None
    assert film.tagline == "Updated genre"
    assert film.short_description == "Updated description."


def test_import_nifff_catalog_keeps_listing_data_when_detail_fetch_fails(db_session: Session, fixture_text_loader, monkeypatch) -> None:
    listing_html = fixture_text_loader("nifff_html/listing_nominal.html")

    monkeypatch.setattr("app.services.import_nifff.build_session", lambda: SimpleNamespace())

    def fake_fetch_html(_session: object, url: str) -> str:
        if "schedule" in url:
            return listing_html
        raise requests.RequestException("detail unavailable")

    monkeypatch.setattr("app.services.import_nifff.fetch_html", fake_fetch_html)

    result = import_nifff_catalog(db=db_session, year=2025)
    film = db_session.scalar(select(Film).where(Film.slug == "a-cure-for-wellness"))

    assert result.films_created == 1
    assert film is not None
    assert film.tagline == "Mind-bending wellness horror"
    assert film.short_description is None


def test_import_nifff_catalog_skips_invalid_cards(db_session: Session, monkeypatch) -> None:
    listing_html = """
    <html>
      <body>
        <div class="card">
          <div>International Competition</div>
          <div>unused line</div>
          <div>Gore Verbinski</div>
          <div>Mind-bending wellness horror</div>
          <div>DE/LU/US, 2016, 146 mins</div>
          <a href="/prog/2025/film/invalid-film"></a>
          <img src="poster.jpg" />
          <p>Enough descriptive text to satisfy the archive card extraction heuristic.</p>
        </div>
      </body>
    </html>
    """

    monkeypatch.setattr("app.services.import_nifff.build_session", lambda: SimpleNamespace())
    monkeypatch.setattr("app.services.import_nifff.fetch_html", lambda _session, _url: listing_html)

    result = import_nifff_catalog(db=db_session, year=2025)

    assert result.cycles_created == 0
    assert result.films_created == 0
    assert db_session.scalars(select(Film)).all() == []
