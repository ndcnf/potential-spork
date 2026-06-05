from __future__ import annotations

import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.schemas.imports import ImportSummary
from app.sources.nifff_html.client import build_session, fetch_html
from app.sources.nifff_html.parser import ParsedFilm, enrich_from_detail, extract_archive_cards, parse_listing_card, slugify
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def _enrich_with_detail_if_available(session: requests.Session, parsed: ParsedFilm) -> ParsedFilm:
    try:
        detail_html = fetch_html(session, parsed.source_url)
    except requests.RequestException as exc:
        logger.warning(
            "NIFFF detail fetch failed; keeping listing data",
            extra={"source_url": parsed.source_url, "film_slug": parsed.slug, "error": str(exc)},
        )
        return parsed

    return enrich_from_detail(detail_html, parsed)


def import_nifff_catalog(db: Session, year: int, schedule_url: str | None = None) -> ImportSummary:
    url = schedule_url or f"https://nifff.ch/archives/{year}/schedule?type=film"
    session = build_session()
    listing_html = fetch_html(session, url)
    soup = BeautifulSoup(listing_html, "html.parser")

    cards = extract_archive_cards(soup, year)
    cycles_created = 0
    films_created = 0
    films_updated = 0

    for card in cards:
        parsed = parse_listing_card(card, url, year)
        if parsed is None:
            continue

        parsed = _enrich_with_detail_if_available(session, parsed)

        cycle = None
        if parsed.cycle_name:
            cycle_slug = slugify(parsed.cycle_name)
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
        film.premiere_label = parsed.premiere_label
        film.short_description = parsed.short_description
        film.cast = parsed.cast
        film.synopsis = parsed.synopsis
        film.language = parsed.language
        film.age_rating = parsed.age_rating
        film.poster_url = parsed.poster_url
        film.source_url = parsed.source_url
        film.cycle_id = cycle.id if cycle else None

        db.add(film)

    db.commit()
    return ImportSummary(cycles_created=cycles_created, films_created=films_created, films_updated=films_updated)
