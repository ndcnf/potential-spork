from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from app.sources.nifff_html.parser import (
    ParsedFilm,
    ParsedScreening,
    extract_screenings_from_detail,
    extract_listing_screenings,
    extract_program_path,
    clean_text,
    enrich_from_detail,
    extract_archive_cards,
    extract_poster_url,
    extract_runtime,
    extract_short_description,
    extract_table_value,
    extract_year,
    field_after_heading,
    parse_listing_card,
    parse_listing_screening_line,
    slugify,
)


def test_slugify_normalizes_text() -> None:
    assert slugify("A Cure for Wellness!!!") == "a-cure-for-wellness"


def test_slugify_returns_unknown_for_empty_value() -> None:
    assert slugify("!!!") == "unknown"


def test_extract_runtime_reads_minutes() -> None:
    assert extract_runtime("2h26 · 146 minutes") == 146
    assert extract_runtime("146 mins") == 146
    assert extract_runtime(None) is None


def test_extract_runtime_returns_none_for_unrecognized_format() -> None:
    assert extract_runtime("2h26") is None


def test_extract_year_reads_four_digit_year() -> None:
    assert extract_year("DE/LU/US, 2016, 146 mins") == 2016
    assert extract_year(None) is None


def test_clean_text_joins_strings() -> None:
    soup = BeautifulSoup("<p> Hello <strong>world</strong> </p>", "html.parser")

    assert clean_text(soup.p) == "Hello world"


def test_field_after_heading_returns_following_block_text() -> None:
    html = """
    <section>
      <h2>Pays</h2>
      <p>DE/LU/US</p>
    </section>
    """
    soup = BeautifulSoup(html, "html.parser")

    assert field_after_heading(soup, "Pays") == "DE/LU/US"


def test_extract_table_value_reads_value_from_table() -> None:
    html = """
    <table>
      <tr><th>Distribution</th></tr>
      <tr><td>Dane DeHaan, Mia Goth</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")

    assert extract_table_value(soup, "Distribution") == "Dane DeHaan, Mia Goth"


def test_extract_poster_url_prefers_header_image_data_src() -> None:
    html = '<div class="header-page__image"><img data-src="/images/poster.jpg" /></div>'
    soup = BeautifulSoup(html, "html.parser")

    assert extract_poster_url(soup, "https://nifff.ch/prog/2025/film/a-cure-for-wellness") == "https://nifff.ch/images/poster.jpg"


def test_extract_poster_url_falls_back_to_og_image() -> None:
    html = '<meta property="og:image" content="/images/og.jpg" />'
    soup = BeautifulSoup(html, "html.parser")

    assert extract_poster_url(soup, "https://nifff.ch/prog/2025/film/a-cure-for-wellness") == "https://nifff.ch/images/og.jpg"


def test_extract_poster_url_prefers_lazy_source_over_svg_placeholder() -> None:
    html = """
    <img
      src="data:image/svg+xml,%3Csvg%3E%3C/svg%3E"
      data-lazy-src="https://web.archive.org/web/20250704120326/https://files.eventival.com/poster.jpeg"
    />
    """
    soup = BeautifulSoup(html, "html.parser")

    assert (
        extract_poster_url(soup, "https://web.archive.org/web/20250704120326/https://nifff.ch/programme/")
        == "https://web.archive.org/web/20250704120326/https://files.eventival.com/poster.jpeg"
    )


def test_extract_short_description_falls_back_to_meta_description() -> None:
    html = '<meta name="description" content="Short description." />'
    soup = BeautifulSoup(html, "html.parser")

    assert extract_short_description(soup) == "Short description."


def test_extract_screenings_from_detail_reads_screening_nodes() -> None:
    html = """
    <div class="screening" data-screening-start="2025-07-05T18:00:00+02:00" data-screening-end="2025-07-05T20:00:00+02:00" data-venue-name="Théâtre" data-source-url="/screenings/1" data-ticket-url="/tickets/1"></div>
    """
    soup = BeautifulSoup(html, "html.parser")

    screenings = extract_screenings_from_detail(soup, "https://nifff.ch/prog/2025/film/a-cure-for-wellness")

    assert len(screenings) == 1
    assert screenings[0].venue_name == "Théâtre"
    assert screenings[0].source_url == "https://nifff.ch/screenings/1"
    assert screenings[0].ticket_url == "https://nifff.ch/tickets/1"


def test_enrich_from_detail_keeps_listing_screenings_when_detail_has_none() -> None:
    parsed = ParsedFilm(
        title="A Useful Ghost",
        slug="a-useful-ghost",
        source_url="https://nifff.ch/prog/2025/film/a-useful-ghost",
        screenings=[
            ParsedScreening(
                starts_at=datetime(2025, 7, 5, 19, 0),
                ends_at=None,
                venue_name="Arcades",
            )
        ],
    )

    enriched = enrich_from_detail("<html><body></body></html>", parsed)

    assert len(enriched.screenings) == 1
    assert enriched.screenings[0].venue_name == "Arcades"


def test_extract_program_path_normalizes_wayback_program_url() -> None:
    url = "https://web.archive.org/web/20250704120326/https://nifff.ch/prog/2025/film/a-useful-ghost"

    assert extract_program_path(url) == "/prog/2025/film/a-useful-ghost"


def test_parse_listing_screening_line_reads_inline_listing_screening() -> None:
    screening = parse_listing_screening_line("05.07, Arcades, 19:00", 2025, "https://nifff.ch/prog/2025/film/a-useful-ghost")

    assert screening is not None
    assert screening.venue_name == "Arcades"
    assert screening.starts_at == datetime(2025, 7, 5, 19, 0)


def test_extract_listing_screenings_reads_multiple_lines_from_wayback_card() -> None:
    html = """
    <div class="archive-movie__item">
      <div class="archive-movie__item__information--right">
        <p>05.07, Arcades, 19:00</p>
        <p>08.07, Arcades, 16:30</p>
      </div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    screenings = extract_listing_screenings(
        soup.select_one(".archive-movie__item"),
        2025,
        "https://nifff.ch/prog/2025/film/a-useful-ghost",
    )

    assert len(screenings) == 2
    assert screenings[0].venue_name == "Arcades"
    assert screenings[1].starts_at == datetime(2025, 7, 8, 16, 30)


def test_extract_archive_cards_returns_unique_cards() -> None:
    html = """
    <div class="card">
      <img src="poster.jpg" />
      <a href="/prog/2025/film/a-cure-for-wellness">A Cure for Wellness</a>
      <p>Some descriptive text long enough for the heuristic.</p>
    </div>
    <div class="card">
      <img src="poster2.jpg" />
      <a href="/prog/2025/film/the-substance">The Substance</a>
      <p>Another descriptive text long enough for the heuristic.</p>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    cards = extract_archive_cards(soup, 2025)

    assert len(cards) == 2


def test_parse_listing_card_extracts_expected_fields() -> None:
    html = """
    <div class="card">
      <div>International Competition</div>
      <div>unused line</div>
      <div>Gore Verbinski</div>
      <div>Mind-bending wellness horror</div>
      <div>DE/LU/US, 2016, 146 mins</div>
      <a href="/prog/2025/film/a-cure-for-wellness">A Cure for Wellness</a>
      <img src="poster.jpg" />
      <p>Enough text to make the parent container qualify as a card.</p>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one(".card")

    parsed = parse_listing_card(card, "https://nifff.ch/archives/2025/schedule?type=film", 2025)

    assert parsed is not None
    assert parsed.title == "A Cure for Wellness"
    assert parsed.slug == "a-cure-for-wellness"
    assert parsed.source_url == "https://nifff.ch/prog/2025/film/a-cure-for-wellness"
    assert parsed.cycle_name == "International Competition"
    assert parsed.directors == "Gore Verbinski"
    assert parsed.tagline == "Mind-bending wellness horror"
    assert parsed.year == 2016
    assert parsed.duration_minutes == 146
    assert parsed.countries == "DE/LU/US"


def test_parse_listing_card_returns_none_without_link() -> None:
    soup = BeautifulSoup('<div class="card"><div>No link here</div></div>', "html.parser")

    assert parse_listing_card(soup.select_one(".card"), "https://nifff.ch/archives/2025/schedule?type=film", 2025) is None


def test_parse_listing_card_returns_none_without_title() -> None:
    html = """
    <div class="card">
      <div>International Competition</div>
      <div>unused line</div>
      <div>Gore Verbinski</div>
      <div>Mind-bending wellness horror</div>
      <div>DE/LU/US, 2016, 146 mins</div>
      <a href="/prog/2025/film/a-cure-for-wellness"></a>
      <img src="poster.jpg" />
      <p>Enough text to make the parent container qualify as a card.</p>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    assert parse_listing_card(soup.select_one(".card"), "https://nifff.ch/archives/2025/schedule?type=film", 2025) is None


def test_enrich_from_detail_updates_parsed_film_from_detail_html() -> None:
    parsed = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
        directors="Gore Verbinski",
        year=2016,
        countries="DE/LU/US",
        duration_minutes=146,
        tagline="Mind-bending wellness horror",
    )

    detail_html = """
    <html>
      <head>
        <meta name="description" content="A young executive discovers a terrifying secret." />
        <meta property="og:image" content="/images/cure.jpg" />
      </head>
      <body>
        <div class="header-page">
          <h1>
            A Cure for Wellness
            <small>ignored</small>
            <small>Swiss Premiere</small>
          </h1>
        </div>
        <h2>Section</h2><p>International Competition</p>
        <h2>Année</h2><p>2016</p>
        <h2>Pays</h2><p>DE/LU/US</p>
        <h2>Durée</h2><p>146 minutes</p>
        <h2>Genre</h2><p>Psychological horror</p>
        <h2>Film</h2><p>Extended synopsis text.</p>
        <h2>Langue</h2><p>English</p>
        <h2>Âge</h2><p>16+</p>
        <table>
          <tr><th>Distribution</th></tr>
          <tr><td>Dane DeHaan, Mia Goth</td></tr>
        </table>
      </body>
    </html>
    """

    enriched = enrich_from_detail(detail_html, parsed)

    assert enriched.cycle_name == "International Competition"
    assert enriched.year == 2016
    assert enriched.countries == "DE/LU/US"
    assert enriched.duration_minutes == 146
    assert enriched.tagline == "Psychological horror"
    assert enriched.premiere_label == "Swiss Premiere"
    assert enriched.short_description == "A young executive discovers a terrifying secret."
    assert enriched.cast == "Dane DeHaan, Mia Goth"
    assert enriched.synopsis == "Extended synopsis text."
    assert enriched.language == "English"
    assert enriched.age_rating == "16+"
    assert enriched.poster_url == "https://nifff.ch/images/cure.jpg"
    assert enriched.screenings == []


def test_enrich_from_detail_preserves_existing_values_when_missing() -> None:
    parsed = ParsedFilm(
        title="A Cure for Wellness",
        slug="a-cure-for-wellness",
        source_url="https://nifff.ch/prog/2025/film/a-cure-for-wellness",
        cycle_name="International Competition",
        year=2016,
        countries="DE/LU/US",
        duration_minutes=146,
        tagline="Existing tagline",
    )
    detail_html = "<html><body><h2>Section</h2><p>International Competition</p></body></html>"

    enriched = enrich_from_detail(detail_html, parsed)

    assert enriched.year == 2016
    assert enriched.countries == "DE/LU/US"
    assert enriched.duration_minutes == 146
    assert enriched.tagline == "Existing tagline"
