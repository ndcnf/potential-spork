from pydantic import BaseModel

from app.schemas.common import PlanningType, Priority


class FilmRead(BaseModel):
    id: int
    title: str
    slug: str
    directors: str | None
    year: int | None
    countries: str | None
    duration_minutes: int | None
    tagline: str | None
    premiere_label: str | None
    short_description: str | None
    cast: str | None
    synopsis: str | None
    language: str | None
    age_rating: str | None
    poster_url: str | None
    priority: Priority
    planning_type: PlanningType
    cycle_id: int | None
    cycle_name: str | None = None
    cycle_color: str | None = None


class FilmUpdate(BaseModel):
    priority: Priority | None = None
