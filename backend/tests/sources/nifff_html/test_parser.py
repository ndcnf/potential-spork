from __future__ import annotations

from bs4 import BeautifulSoup

from app.sources.nifff_html.parser import (
    ParsedFilm,
    clean_text,
    enrich_from_detail,
    extract_archive_cards,
    extract_runtime,
    extract_table_value,
    extract_year,
    field_after_heading,
    parse_listing_card,
    slugify,
)


def test_slugify_normalizes_text() -> None:
    assert slugify("A Cure for Wellness!!!") == "a-cure-for-wellness"


def test_extract_runtime_reads_minutes() -> None:
    assert extract_runtime("2h26 · 146 minutes") == 146
    assert extract_runtime("146 mins") == 146
    assert extract_runtime(None) is None


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
