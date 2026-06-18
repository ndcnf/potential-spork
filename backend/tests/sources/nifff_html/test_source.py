from __future__ import annotations

from collections.abc import Callable

import pytest

from app.sources.nifff_html.source import NifffArchiveHtmlSource, NifffHtmlCatalogPayload, NifffLiveHtmlSource


def test_archive_source_fetches_wayback_listing_without_detail_fetch(
    fixture_text_loader: Callable[[str], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fetched_urls: list[str] = []

    def fake_fetch_html(session, url: str) -> str:
        fetched_urls.append(url)
        if len(fetched_urls) > 1:
            raise AssertionError(f"archive source must not fetch detail pages: {url}")
        return fixture_text_loader("nifff_html/listing_wayback_programme.html")

    monkeypatch.setattr("app.sources.nifff_html.source.fetch_html", fake_fetch_html)

    payload = NifffArchiveHtmlSource().fetch_catalog(2025)

    assert fetched_urls == ["https://web.archive.org/web/20250704120326/https://nifff.ch/programme/"]
    assert isinstance(payload, NifffHtmlCatalogPayload)
    parsed_by_slug = {film.slug: film for film in payload.parsed_films}
    assert len(payload.parsed_films) == 2
    assert parsed_by_slug["a-useful-ghost"].title == "A Useful Ghost"
    assert len(parsed_by_slug["a-useful-ghost"].screenings) == 3
    assert parsed_by_slug["asian-shorts"].title == "Asian Shorts"
    assert len(parsed_by_slug["asian-shorts"].screenings) == 2
    assert all(not url.startswith("https://nifff.ch") for url in fetched_urls)


def test_live_source_keeps_live_programme_entrypoint() -> None:
    source = NifffLiveHtmlSource()

    assert source.schedule_url_for_year(2026) == "https://nifff.ch/programme/"


def test_live_source_fetches_listing_without_detail_fetch(
    fixture_text_loader: Callable[[str], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fetched_urls: list[str] = []

    def fake_fetch_html(session, url: str) -> str:
        fetched_urls.append(url)
        if len(fetched_urls) > 1:
            raise AssertionError(f"live source must not block on detail pages during catalog import: {url}")
        return fixture_text_loader("nifff_html/listing_wayback_programme.html").replace("/2025/", "/2026/")

    monkeypatch.setattr("app.sources.nifff_html.source.fetch_html", fake_fetch_html)

    payload = NifffLiveHtmlSource("https://nifff.ch/programme/?").fetch_catalog(2026)

    assert fetched_urls == ["https://nifff.ch/programme/?"]
    assert isinstance(payload, NifffHtmlCatalogPayload)
    assert len(payload.parsed_films) == 2


def test_archive_source_rejects_direct_nifff_url() -> None:
    with pytest.raises(ValueError, match="demo archive source must use Wayback"):
        NifffArchiveHtmlSource("https://nifff.ch/archives/{year}/schedule?type=film")
