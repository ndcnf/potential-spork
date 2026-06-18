from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import requests

from app.sources.nifff_html.client import build_session, fetch_html
from app.sources.nifff_html.parser import ParsedFilm, enrich_from_detail, parse_catalog_html


logger = logging.getLogger(__name__)

NIFFF_LIVE_PROGRAMME_URL = "https://nifff.ch/programme/"
NIFFF_2025_WAYBACK_PROGRAMME_URL = "https://web.archive.org/web/20250704120326/https://nifff.ch/programme/"


@dataclass(slots=True)
class NifffHtmlCatalogPayload:
    parsed_films: list[ParsedFilm]


class BaseNifffHtmlSource:
    source_name = "nifff_html"

    def __init__(self, *, schedule_url_template: str, source_mode: Literal["demo", "prod"], fetch_details: bool) -> None:
        self._schedule_url_template = schedule_url_template
        self.source_mode = source_mode
        self._fetch_details = fetch_details

    def schedule_url_for_year(self, year: int) -> str:
        return self._schedule_url_template.format(year=year)

    def fetch_catalog(self, year: int) -> NifffHtmlCatalogPayload:
        url = self.schedule_url_for_year(year)
        session = build_session()
        listing_html = fetch_html(session, url)
        parsed_films = parse_catalog_html(listing_html, base_url=url, year=year)

        if not self._fetch_details:
            return NifffHtmlCatalogPayload(parsed_films=parsed_films)

        enriched_films: list[ParsedFilm] = []
        for parsed in parsed_films:
            enriched_films.append(self._enrich_with_detail_if_available(session, parsed))

        return NifffHtmlCatalogPayload(parsed_films=enriched_films)

    def _enrich_with_detail_if_available(self, session: requests.Session, parsed: ParsedFilm) -> ParsedFilm:
        try:
            detail_html = fetch_html(session, parsed.source_url)
        except requests.RequestException as exc:
            logger.warning(
                "NIFFF detail fetch failed; keeping listing data",
                extra={
                    "source_url": parsed.source_url,
                    "film_slug": parsed.slug,
                    "error": str(exc),
                    "source_mode": self.source_mode,
                },
            )
            return parsed

        return enrich_from_detail(detail_html, parsed)


class NifffArchiveHtmlSource(BaseNifffHtmlSource):
    def __init__(self, schedule_url_template: str = NIFFF_2025_WAYBACK_PROGRAMME_URL) -> None:
        if "nifff.ch" in schedule_url_template and "web.archive.org" not in schedule_url_template:
            raise ValueError("demo archive source must use Wayback instead of direct nifff.ch URLs")
        super().__init__(schedule_url_template=schedule_url_template, source_mode="demo", fetch_details=False)


class NifffLiveHtmlSource(BaseNifffHtmlSource):
    def __init__(self, schedule_url_template: str = NIFFF_LIVE_PROGRAMME_URL) -> None:
        super().__init__(schedule_url_template=schedule_url_template, source_mode="prod", fetch_details=False)


class NifffHtmlSource(NifffArchiveHtmlSource):
    """Backward-compatible alias while the service still defaults to archive/demo mode."""
