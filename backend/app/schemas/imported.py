from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.common import PlanningType


@dataclass(slots=True)
class ImportedCycle:
    source_key: str
    name: str
    slug: str
    color: str | None = None


@dataclass(slots=True)
class ImportedFilm:
    source_key: str
    title: str
    slug: str
    source_url: str | None
    cycle_source_key: str | None
    directors: str | None = None
    year: int | None = None
    countries: str | None = None
    duration_minutes: int | None = None
    tagline: str | None = None
    premiere_label: str | None = None
    short_description: str | None = None
    cast: str | None = None
    synopsis: str | None = None
    language: str | None = None
    age_rating: str | None = None
    poster_url: str | None = None
    planning_type: PlanningType = "standalone"


@dataclass(slots=True)
class ImportedVenue:
    source_key: str
    name: str


@dataclass(slots=True)
class ImportedScreening:
    source_key: str
    film_source_key: str
    venue_source_key: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    source_url: str | None = None
    ticket_url: str | None = None


@dataclass(slots=True)
class CanonicalImportBundle:
    source_name: str
    year: int
    cycles: list[ImportedCycle] = field(default_factory=list)
    films: list[ImportedFilm] = field(default_factory=list)
    venues: list[ImportedVenue] = field(default_factory=list)
    screenings: list[ImportedScreening] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImportReport:
    source_name: str
    year: int
    cycles_created: int = 0
    cycles_updated: int = 0
    films_created: int = 0
    films_updated: int = 0
    venues_created: int = 0
    venues_updated: int = 0
    screenings_created: int = 0
    screenings_updated: int = 0
    screenings_pruned: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
