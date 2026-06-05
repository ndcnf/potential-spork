from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from app.sources.nifff_html.client import build_session, fetch_html
from app.sources.nifff_html.parser import ParsedFilm, enrich_from_detail, extract_archive_cards, parse_listing_card


logger = logging.getLogger(__name__)


class NifffHtmlSource:
    source_name = "nifff_html"

    def __init__(self, schedule_url_template: str = "https://nifff.ch/archives/{year}/schedule?type=film") -> None:
        self._schedule_url_template = schedule_url_template

    def fetch_catalog(self, year: int) -> list[ParsedFilm]:
        url = self._schedule_url_template.format(year=year)
        session = build_session()
        listing_html = fetch_html(session, url)
        soup = BeautifulSoup(listing_html, "html.parser")
        cards = extract_archive_cards(soup, year)

        parsed_films: list[ParsedFilm] = []
        for card in cards:
            parsed = parse_listing_card(card, url, year)
            if parsed is None:
                continue
            parsed_films.append(self._enrich_with_detail_if_available(session, parsed))

        return parsed_films

    def _enrich_with_detail_if_available(self, session: requests.Session, parsed: ParsedFilm) -> ParsedFilm:
        try:
            detail_html = fetch_html(session, parsed.source_url)
        except requests.RequestException as exc:
            logger.warning(
                "NIFFF detail fetch failed; keeping listing data",
                extra={"source_url": parsed.source_url, "film_slug": parsed.slug, "error": str(exc)},
            )
            return parsed

        return enrich_from_detail(detail_html, parsed)
