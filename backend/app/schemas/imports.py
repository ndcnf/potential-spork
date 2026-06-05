from pydantic import BaseModel, HttpUrl


class ImportCatalogPayload(BaseModel):
    year: int = 2025
    schedule_url: HttpUrl | None = None


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
