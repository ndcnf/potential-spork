from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.schemas.imports import ImportSummary


USER_AGENT = "potential-spork/0.1 (+https://github.com/)"


@dataclass
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
    cast: str | None = None
    synopsis: str | None = None
    language: str | None = None
    age_rating: str | None = None


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def _clean_text(node: Tag | None) -> str | None:
    if node is None:
        return None
    text = " ".join(node.stripped_strings)
    return text or None


def _extract_runtime(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d+)\s*(?:minutes|mins|')", value)
    return int(match.group(1)) if match else None


def _extract_year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(19|20)\d{2}", value)
    return int(match.group(0)) if match else None


def _field_after_heading(soup: BeautifulSoup, heading: str) -> str | None:
    header = soup.find(lambda tag: tag.name in {"h2", "h3"} and tag.get_text(strip=True).lower() == heading.lower())
    if header is None:
        return None
    sibling = header.find_next_sibling()
    while sibling is not None and getattr(sibling, "name", None) is None:
        sibling = sibling.find_next_sibling()
    return _clean_text(sibling) if sibling else None


def _extract_archive_cards(soup: BeautifulSoup, year: int) -> list[Tag]:
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


def _parse_listing_card(card: Tag, base_url: str, year: int) -> ParsedFilm | None:
    link = card.select_one(f'a[href*="/prog/{year}/film/"]')
    if link is None or not link.get("href"):
        return None

    source_url = urljoin(base_url, link["href"])
    title = _clean_text(link) or _clean_text(card.find(["h2", "h3"]))
    if not title:
        return None

    text_lines = [text.strip() for text in card.stripped_strings if text.strip()]
    cycle_name = text_lines[0] if text_lines else None
    directors = text_lines[2] if len(text_lines) > 2 else None
    tagline = text_lines[3] if len(text_lines) > 3 else None
    info_line = next((line for line in text_lines if re.search(r"(19|20)\d{2}", line) and re.search(r"\d+['m]", line)), None)

    return ParsedFilm(
        title=title,
        slug=_slugify(source_url.rstrip("/").split("/")[-1]),
        source_url=source_url,
        cycle_name=cycle_name,
        directors=directors,
        year=_extract_year(info_line),
        countries=info_line.split(",")[0] if info_line and "," in info_line else None,
        duration_minutes=_extract_runtime(info_line),
        tagline=tagline,
    )


def _enrich_from_detail(session: requests.Session, parsed: ParsedFilm) -> ParsedFilm:
    response = session.get(parsed.source_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    return ParsedFilm(
        title=parsed.title,
        slug=parsed.slug,
        source_url=parsed.source_url,
        cycle_name=_field_after_heading(soup, "Section") or parsed.cycle_name,
        directors=parsed.directors,
        year=_extract_year(_field_after_heading(soup, "Année")) or parsed.year,
        countries=_field_after_heading(soup, "Pays") or parsed.countries,
        duration_minutes=_extract_runtime(_field_after_heading(soup, "Durée")) or parsed.duration_minutes,
        tagline=_field_after_heading(soup, "Genre") or parsed.tagline,
        cast=_field_after_heading(soup, "Distribution"),
        synopsis=_field_after_heading(soup, "Film"),
        language=_field_after_heading(soup, "Langue"),
        age_rating=_field_after_heading(soup, "Âge"),
    )


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    url = schedule_url or f"https://nifff.ch/archives/{year}/schedule?type=film"
    session = _session()
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    cards = _extract_archive_cards(soup, year)
    cycles_created = 0
    films_created = 0
    films_updated = 0

    for card in cards:
        parsed = _parse_listing_card(card, url, year)
        if parsed is None:
            continue

        try:
            parsed = _enrich_from_detail(session, parsed)
        except requests.RequestException:
            pass

        cycle = None
        if parsed.cycle_name:
            cycle_slug = _slugify(parsed.cycle_name)
            cycle = db.scalar(select(Cycle).where(Cycle.slug == cycle_slug))
            if cycle is None:
                cycle = Cycle(name=parsed.cycle_name, slug=cycle_slug)
                db.add(cycle)
                db.flush()
                cycles_created += 1

        film = db.scalar(select(Film).where(Film.slug == parsed.slug))
        if film is None:
            film = Film(title=parsed.title, slug=parsed.slug, priority="medium")
            films_created += 1
        else:
            films_updated += 1

        film.title = parsed.title
        film.directors = parsed.directors
        film.year = parsed.year
        film.countries = parsed.countries
        film.duration_minutes = parsed.duration_minutes
        film.tagline = parsed.tagline
        film.cast = parsed.cast
        film.synopsis = parsed.synopsis
        film.language = parsed.language
        film.age_rating = parsed.age_rating
        film.source_url = parsed.source_url
        film.cycle_id = cycle.id if cycle else None

        db.add(film)

    db.commit()
    return ImportSummary(cycles_created=cycles_created, films_created=films_created, films_updated=films_updated)
