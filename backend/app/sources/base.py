from __future__ import annotations

from typing import Literal
from typing import Protocol


class FestivalSource(Protocol):
    source_name: str
    source_mode: Literal["demo", "prod"]

    def fetch_catalog(self, year: int) -> object:
        """Fetches raw catalog data from the remote source."""
