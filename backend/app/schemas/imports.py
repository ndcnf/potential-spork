from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ImportCatalogPayload(BaseModel):
    year: int = 2025
    schedule_url: HttpUrl | None = None
    source_mode: Literal["demo", "prod"] = "demo"


class ImportSummary(BaseModel):
    cycles_created: int
    films_created: int
    films_updated: int
    venues_created: int = 0
    venues_updated: int = 0
    screenings_created: int = 0
    screenings_updated: int = 0
    warnings_count: int = 0
    errors_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
