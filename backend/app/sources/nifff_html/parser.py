from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag


@dataclass(slots=True)
class ParsedFilm:
    title: str
    slug: str
    source_url: str
    cycle_name: str | None = None
    directors: str | None = None
    year: int | None = None
    countries: str | None = None
    duration_minutes: int | None = None
    tagline: str | None = None
    premiere_label: str | None = None
    short_description: str | None = None
    cast: str | None = None
    synopsis: str | None = None
    language: str | None = None
    age_rating: str | None = None
    poster_url: str | None = None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def clean_text(node: Tag | None) -> str | None:
    if node is None:
        return None
    text = " ".join(node.stripped_strings)
    return text or None


def extract_runtime(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d+)\s*(?:minutes|mins|')", value)
    return int(match.group(1)) if match else None


def extract_year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(19|20)\d{2}", value)
    return int(match.group(0)) if match else None


def field_after_heading(soup: BeautifulSoup, heading: str) -> str | None:
    header = soup.find(lambda tag: tag.name in {"h2", "h3"} and tag.get_text(strip=True).lower() == heading.lower())
    if header is None:
        return None
    sibling = header.find_next_sibling()
    while sibling is not None and getattr(sibling, "name", None) is None:
        sibling = sibling.find_next_sibling()
    return clean_text(sibling) if sibling else None


def extract_table_value(soup: BeautifulSoup, heading: str) -> str | None:
    for header in soup.select("table th"):
        if header.get_text(" ", strip=True).lower() != heading.lower():
            continue

        row = header.find_parent("tr")
        next_row = row.find_next_sibling("tr") if row else None
        value_cell = next_row.find("td") if next_row else None
        return clean_text(value_cell)

    return None


def extract_poster_url(soup: BeautifulSoup, base_url: str) -> str | None:
    header_image = soup.select_one('.header-page__image img[data-src], .header-page__image img[src], .ratio-16-9 img[data-src], .ratio-16-9 img[src]')
    if header_image is not None:
        src = header_image.get("data-src") or header_image.get("src")
        if src:
            return urljoin(base_url, src)

    meta = soup.find("meta", property="og:image")
    if meta is not None and meta.get("content"):
        return urljoin(base_url, meta["content"])

    image = soup.select_one("img[src]")
    if image is not None and image.get("src"):
        return urljoin(base_url, image["src"])

    return None


def extract_premiere_label(soup: BeautifulSoup) -> str | None:
    title = soup.select_one(".header-page h1")
    if title is None:
        return None

    labels = title.select("small")
    if len(labels) >= 2:
        text = clean_text(labels[1])
        return text or None

    return None


def extract_short_description(soup: BeautifulSoup) -> str | None:
    paragraph = soup.select_one('.header-page .row.mb-eighth p, .header-page .row.mb-lg-third p')
    if paragraph is not None:
        return clean_text(paragraph)

    meta = soup.find("meta", attrs={"name": "description"})
    if meta is not None and meta.get("content"):
        return meta["content"].strip()

    return None


def extract_archive_cards(soup: BeautifulSoup, year: int) -> list[Tag]:
    links = soup.select(f'a[href*="/prog/{year}/film/"]')
    cards: list[Tag] = []
    seen: set[int] = set()

    for link in links:
        card = link
        for _ in range(6):
            if card.parent is None:
                break
            card = card.parent
            if card.find("img") and len(card.get_text(" ", strip=True)) > 30:
                break
        if id(card) not in seen:
            seen.add(id(card))
            cards.append(card)
    return cards


def parse_listing_card(card: Tag, base_url: str, year: int) -> ParsedFilm | None:
    link = card.select_one(f'a[href*="/prog/{year}/film/"]')
    if link is None or not link.get("href"):
        return None

    source_url = urljoin(base_url, link["href"])
    title = clean_text(link) or clean_text(card.find(["h2", "h3"]))
    if not title:
        return None

    text_lines = [text.strip() for text in card.stripped_strings if text.strip()]
    cycle_name = text_lines[0] if text_lines else None
    directors = text_lines[2] if len(text_lines) > 2 else None
    tagline = text_lines[3] if len(text_lines) > 3 else None
    info_line = next((line for line in text_lines if re.search(r"(19|20)\d{2}", line) and re.search(r"\d+\s*(?:'|m|min|mins|minutes)", line)), None)

    return ParsedFilm(
        title=title,
        slug=slugify(source_url.rstrip("/").split("/")[-1]),
        source_url=source_url,
        cycle_name=cycle_name,
        directors=directors,
        year=extract_year(info_line),
        countries=info_line.split(",")[0] if info_line and "," in info_line else None,
        duration_minutes=extract_runtime(info_line),
        tagline=tagline,
    )


def enrich_from_detail(html: str, parsed: ParsedFilm) -> ParsedFilm:
    soup = BeautifulSoup(html, "html.parser")

    return ParsedFilm(
        title=parsed.title,
        slug=parsed.slug,
        source_url=parsed.source_url,
        cycle_name=field_after_heading(soup, "Section") or parsed.cycle_name,
        directors=parsed.directors,
        year=extract_year(field_after_heading(soup, "Année")) or parsed.year,
        countries=field_after_heading(soup, "Pays") or parsed.countries,
        duration_minutes=extract_runtime(field_after_heading(soup, "Durée")) or parsed.duration_minutes,
        tagline=field_after_heading(soup, "Genre") or parsed.tagline,
        premiere_label=extract_premiere_label(soup),
        short_description=extract_short_description(soup),
        cast=extract_table_value(soup, "Distribution") or field_after_heading(soup, "Distribution"),
        synopsis=field_after_heading(soup, "Film"),
        language=field_after_heading(soup, "Langue"),
        age_rating=field_after_heading(soup, "Âge"),
        poster_url=extract_poster_url(soup, parsed.source_url),
    )
