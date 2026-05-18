from pydantic import BaseModel, HttpUrl


class ImportCatalogPayload(BaseModel):
    year: int = 2025
    schedule_url: HttpUrl | None = None


class ImportSummary(BaseModel):
    cycles_created: int
    films_created: int
    films_updated: int
