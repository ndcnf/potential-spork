from pydantic import BaseModel

from app.schemas.common import Priority


class FilmRead(BaseModel):
    id: int
    title: str
    slug: str
    directors: str | None
    year: int | None
    countries: str | None
    duration_minutes: int | None
    tagline: str | None
    cast: str | None
    synopsis: str | None
    language: str | None
    age_rating: str | None
    priority: Priority
    cycle_id: int | None
    cycle_name: str | None = None
    cycle_color: str | None = None


class FilmUpdate(BaseModel):
    priority: Priority | None = None
