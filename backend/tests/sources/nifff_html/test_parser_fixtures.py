from __future__ import annotations

from bs4 import BeautifulSoup

from app.sources.nifff_html.parser import ParsedFilm, enrich_from_detail, extract_archive_cards, parse_listing_card


def test_listing_snapshot_extracts_expected_number_of_cards(fixture_text_loader) -> None:
    html = fixture_text_loader("nifff_html/listing_nominal.html")
    soup = BeautifulSoup(html, "html.parser")

    cards = extract_archive_cards(soup, 2025)

    assert len(cards) == 1


def test_listing_snapshot_parses_expected_film_fields(fixture_text_loader) -> None:
    html = fixture_text_loader("nifff_html/listing_nominal.html")
    soup = BeautifulSoup(html, "html.parser")
    card = extract_archive_cards(soup, 2025)[0]

    parsed = parse_listing_card(card, "https://nifff.ch/archives/2025/schedule?type=film", 2025)

    assert parsed is not None
    assert parsed.title == "A Cure for Wellness"
    assert parsed.slug == "a-cure-for-wellness"
    assert parsed.cycle_name == "International Competition"


def test_detail_snapshot_extracts_expected_optional_fields(fixture_text_loader) -> None:
    parsed = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
    )
    html = fixture_text_loader("nifff_html/detail_nominal.html")

    enriched = enrich_from_detail(html, parsed)

    assert enriched.short_description == "A young executive discovers a terrifying secret."
    assert enriched.cast == "Dane DeHaan, Mia Goth"
    assert enriched.poster_url == "https://nifff.ch/images/cure.jpg"
    assert len(enriched.screenings) == 1
    assert enriched.screenings[0].venue_name == "Théâtre"


def test_detail_snapshot_tolerates_missing_distribution(fixture_text_loader) -> None:
    parsed = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
    )
    html = fixture_text_loader("nifff_html/detail_missing_distribution.html")

    enriched = enrich_from_detail(html, parsed)

    assert enriched.cast is None
    assert enriched.short_description == "A young executive discovers a terrifying secret."


def test_detail_snapshot_tolerates_missing_poster(fixture_text_loader) -> None:
    parsed = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
    )
    html = fixture_text_loader("nifff_html/detail_missing_poster.html")

    enriched = enrich_from_detail(html, parsed)

    assert enriched.poster_url is None


def test_listing_snapshot_returns_none_when_title_missing(fixture_text_loader) -> None:
    html = fixture_text_loader("nifff_html/listing_missing_title.html")
    soup = BeautifulSoup(html, "html.parser")
    card = extract_archive_cards(soup, 2025)[0]

    parsed = parse_listing_card(card, "https://nifff.ch/archives/2025/schedule?type=film", 2025)

    assert parsed is None
