from __future__ import annotations

from app.schemas.imported import CanonicalImportBundle
from app.services.import_catalog import import_catalog, normalize_source_payload
from app.sources.nifff_html.parser import ParsedFilm


class FakeNifffHtmlSource:
    source_name = "nifff_html"

    def fetch_catalog(self, year: int) -> list[ParsedFilm]:
        return [
            ParsedFilm(
                title="A Cure for Wellness",
                slug="a-cure-for-wellness",
                source_url=f"https://nifff.ch/prog/{year}/film/a-cure-for-wellness",
                cycle_name="International Competition",
                directors="Gore Verbinski",
                year=2016,
            )
        ]


def test_normalize_source_payload_builds_canonical_bundle() -> None:
    raw_payload = FakeNifffHtmlSource().fetch_catalog(2025)

    bundle = normalize_source_payload(source_name="nifff_html", raw_payload=raw_payload, year=2025)

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
    assert report.warnings == []
