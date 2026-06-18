from __future__ import annotations

from datetime import datetime

from app.schemas.imported import CanonicalImportBundle
import pytest

from app.services.import_catalog import EmptyCatalogError, import_catalog, normalize_source_payload
from app.sources.nifff_html.parser import ParsedFilm, ParsedScreening
from app.sources.nifff_html.source import NifffHtmlCatalogPayload


class FakeNifffHtmlSource:
    source_name = "nifff_html"
    source_mode = "demo"

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        return NifffHtmlCatalogPayload(
            parsed_films=[
                ParsedFilm(
                    title="A Cure for Wellness",
                    slug="a-cure-for-wellness",
                    source_url=f"https://nifff.ch/prog/{year}/film/a-cure-for-wellness",
                    cycle_name="International Competition",
                    directors="Gore Verbinski",
                    year=2016,
                )
            ]
        )


class FakeNifffHtmlSourceWithInferredScreeningEnd:
    source_name = "nifff_html"
    source_mode = "demo"

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        return NifffHtmlCatalogPayload(
            parsed_films=[
                ParsedFilm(
                    title="A Useful Ghost",
                    slug="a-useful-ghost",
                    source_url=f"https://nifff.ch/prog/{year}/film/a-useful-ghost",
                    duration_minutes=130,
                    screenings=[
                        ParsedScreening(
                            starts_at=datetime.fromisoformat("2025-07-05T19:00:00+02:00"),
                            ends_at=None,
                            venue_name="Arcades",
                        )
                    ],
                )
            ]
        )


class FakeEmptyLiveNifffHtmlSource:
    source_name = "nifff_html"
    source_mode = "prod"

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        return NifffHtmlCatalogPayload(parsed_films=[])


class FakeEmptyDemoNifffHtmlSource:
    source_name = "nifff_html"
    source_mode = "demo"

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        return NifffHtmlCatalogPayload(parsed_films=[])


def test_normalize_source_payload_builds_canonical_bundle() -> None:
    payload = FakeNifffHtmlSource().fetch_catalog(2025)

    bundle = normalize_source_payload(source_name="nifff_html", payload=payload, year=2025)

    assert isinstance(bundle, CanonicalImportBundle)
    assert bundle.source_name == "nifff_html"
    assert len(bundle.cycles) == 1
    assert len(bundle.films) == 1
    assert bundle.films[0].source_key == "nifff:film:a-cure-for-wellness"


def test_import_catalog_returns_bundle_and_report() -> None:
    bundle, report = import_catalog(source=FakeNifffHtmlSource(), year=2025)

    assert bundle.source_name == "nifff_html"
    assert report.source_name == "nifff_html"
    assert report.year == 2025
    assert report.cycles_created == 0
    assert report.screenings_created == 0
    assert report.warnings == []


def test_import_catalog_copies_normalizer_warnings_to_report() -> None:
    bundle, report = import_catalog(source=FakeNifffHtmlSourceWithInferredScreeningEnd(), year=2025)

    assert bundle.warnings == [
        "Inferred screening end from film duration: film=a-useful-ghost starts_at=2025-07-05T19:00:00+02:00"
    ]
    assert report.warnings == bundle.warnings


def test_import_catalog_rejects_empty_live_catalog() -> None:
    with pytest.raises(EmptyCatalogError, match="aucun film"):
        import_catalog(source=FakeEmptyLiveNifffHtmlSource(), year=2025)


def test_import_catalog_allows_empty_demo_catalog() -> None:
    bundle, report = import_catalog(source=FakeEmptyDemoNifffHtmlSource(), year=2025)

    assert bundle.films == []
    assert report.warnings == []
