from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.core.festival_time import real_datetime_from_festival_day


@dataclass(slots=True)
class ParsedScreening:
    starts_at: datetime | None
    ends_at: datetime | None
    venue_name: str | None = None
    ticket_url: str | None = None
    source_url: str | None = None


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
    screenings: list[ParsedScreening] = field(default_factory=list)


WAYBACK_PREFIX_RE = re.compile(r"https?://web\.archive\.org/web/\d+(?:[a-z_]+)?/")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
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


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def normalize_wayback_url(url: str) -> str:
    return WAYBACK_PREFIX_RE.sub("https://", url, count=1)


def is_placeholder_image_url(url: str | None) -> bool:
    return bool(url and url.startswith("data:image/svg+xml"))


def first_real_image_url(image: Tag) -> str | None:
    for attribute in ("data-src", "data-lazy-src", "src"):
        url = image.get(attribute)
        if url and not is_placeholder_image_url(url):
            return url
    return None


def extract_program_path(url: str) -> str:
    normalized_url = normalize_wayback_url(url)
    match = re.search(r"https?://[^/]+(?P<path>/prog/\d+/(?:film|event|film-package)/[^?#/]+)", normalized_url)
    return match.group("path") if match else normalized_url


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


def extract_poster_url(soup: BeautifulSoup | Tag, base_url: str) -> str | None:
    header_image = soup.select_one(
        ".header-page__image img[data-src], .header-page__image img[data-lazy-src], .header-page__image img[src], "
        ".ratio-16-9 img[data-src], .ratio-16-9 img[data-lazy-src], .ratio-16-9 img[src]"
    )
    if header_image is not None:
        src = first_real_image_url(header_image)
        if src:
            return urljoin(base_url, src)

    meta = soup.find("meta", property="og:image")
    if meta is not None and meta.get("content"):
        return urljoin(base_url, meta["content"])

    image = soup.select_one("img[data-src], img[data-lazy-src], img[src]")
    if image is not None:
        src = first_real_image_url(image)
        if src:
            return urljoin(base_url, src)

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
    archive_items = soup.select(".archive-movie__list > .archive-movie__item")
    if archive_items:
        return archive_items

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


def parse_catalog_html(html: str, *, base_url: str, year: int) -> list[ParsedFilm]:
    soup = BeautifulSoup(html, "html.parser")
    parsed_films: list[ParsedFilm] = []

    for card in extract_archive_cards(soup, year):
        parsed = parse_listing_card(card, base_url, year)
        if parsed is not None:
            parsed_films.append(parsed)

    return parsed_films


def parse_listing_screening_line(value: str, year: int, base_url: str) -> ParsedScreening | None:
    text = " ".join(value.split())
    match = re.match(r"(?P<day>\d{2})\.(?P<month>\d{2}),\s*(?P<venue>.+?),\s*(?P<hour>\d{2}):(\d{2})$", text)
    if match is None:
        return None

    hour_minute = re.search(r"(?P<hour>\d{2}):(?P<minute>\d{2})$", text)
    if hour_minute is None:
        return None

    starts_at = real_datetime_from_festival_day(
        year=year,
        month=int(match.group("month")),
        day=int(match.group("day")),
        hour=int(hour_minute.group("hour")),
        minute=int(hour_minute.group("minute")),
    )
    return ParsedScreening(
        starts_at=starts_at,
        ends_at=None,
        venue_name=match.group("venue").strip(),
        source_url=normalize_wayback_url(base_url),
    )


def extract_listing_screenings(card: Tag, year: int, base_url: str) -> list[ParsedScreening]:
    screenings: list[ParsedScreening] = []
    for node in card.select(".archive-movie__item__information--right p"):
        text = clean_text(node)
        screening = parse_listing_screening_line(text, year, base_url) if text else None
        if screening is not None:
            screenings.append(screening)
    return screenings


def extract_title_without_director(title_node: Tag) -> str | None:
    title_fragments: list[str] = []
    for child in title_node.children:
        if isinstance(child, Tag) and "d-block" in (child.get("class") or []):
            continue
        text = child.get_text(" ", strip=True) if isinstance(child, Tag) else str(child).strip()
        if text:
            title_fragments.append(text)

    title = " ".join(title_fragments).strip()
    return title or None


def extract_screenings_from_detail(soup: BeautifulSoup, base_url: str) -> list[ParsedScreening]:
    screening_nodes = soup.select("[data-screening-start], .screening")
    screenings: list[ParsedScreening] = []
    seen: set[tuple[datetime | None, str | None, str | None]] = set()

    for node in screening_nodes:
        starts_at = parse_iso_datetime(node.get("data-screening-start"))
        ends_at = parse_iso_datetime(node.get("data-screening-end"))
        venue_name = node.get("data-venue-name") or clean_text(node.select_one(".screening__venue, .venue"))
        ticket_href = node.get("data-ticket-url")
        if ticket_href is None:
            ticket_link = node.select_one('a[href*="ticket"], a[href*="billet"], a[href*="reservation"]')
            ticket_href = ticket_link.get("href") if ticket_link is not None else None

        source_href = node.get("data-source-url")
        if source_href is None:
            source_link = node.select_one('a[href]')
            source_href = source_link.get("href") if source_link is not None else None

        screening = ParsedScreening(
            starts_at=starts_at,
            ends_at=ends_at,
            venue_name=venue_name,
            ticket_url=urljoin(base_url, ticket_href) if ticket_href else None,
            source_url=urljoin(base_url, source_href) if source_href else None,
        )
        screening_key = (screening.starts_at, screening.venue_name, screening.source_url)
        if screening_key in seen:
            continue
        seen.add(screening_key)
        screenings.append(screening)

    return screenings


def parse_listing_card(card: Tag, base_url: str, year: int) -> ParsedFilm | None:
    link = card.select_one(f'a.cover[href*="/prog/{year}/"], a[href*="/prog/{year}/"]')
    if link is None or not link.get("href"):
        return None

    program_path = extract_program_path(urljoin(base_url, link["href"]))
    is_film = f"/prog/{year}/film/" in program_path
    is_film_package = f"/prog/{year}/film-package/" in program_path
    if not is_film and not is_film_package:
        return None

    source_url = f"https://nifff.ch{program_path}" if program_path.startswith("/") else program_path
    title_node = card.select_one(".archive-movie__item__title")
    director_node = card.select_one(".archive-movie__item__title .d-block")
    title = extract_title_without_director(title_node) if title_node is not None else None
    if not title:
        title = clean_text(link) or clean_text(card.find(["h2", "h3"]))
    if not title:
        return None

    text_lines = [text.strip() for text in card.stripped_strings if text.strip()]
    categories_node = card.select_one(".archive-movie__item__categories")
    info_left_node = card.select_one(".archive-movie__item__information--left")
    info_left = clean_text(info_left_node)
    genre_node = card.select_one(".archive-movie__item__genre")

    cycle_name = clean_text(categories_node) or (text_lines[0] if text_lines else None)
    directors = clean_text(director_node) or (text_lines[2] if len(text_lines) > 2 else None)
    tagline = clean_text(genre_node) or (text_lines[3] if len(text_lines) > 3 else None)
    info_line = info_left or next((line for line in text_lines if re.search(r"(19|20)\d{2}", line) and re.search(r"\d+\s*(?:'|m|min|mins|minutes)", line)), None)
    premiere_label = None
    if info_left_node is not None:
        info_parts = [part.strip() for part in info_left_node.stripped_strings if part.strip()]
        premiere_label = info_parts[1] if len(info_parts) > 1 else None

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
        premiere_label=premiere_label,
        poster_url=extract_poster_url(card, base_url),
        screenings=extract_listing_screenings(card, year, source_url),
    )


def enrich_from_detail(html: str, parsed: ParsedFilm) -> ParsedFilm:
    soup = BeautifulSoup(html, "html.parser")
    detail_screenings = extract_screenings_from_detail(soup, parsed.source_url)

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
        screenings=detail_screenings or parsed.screenings,
    )
