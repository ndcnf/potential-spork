from __future__ import annotations

from typing import Literal, Protocol, TypeAlias


CatalogPayload: TypeAlias = object


class FestivalSource(Protocol):
    source_name: str
    source_mode: Literal["demo", "prod"]

    def fetch_catalog(self, year: int) -> CatalogPayload:
        """Fetches a source-specific catalog payload for normalization."""
