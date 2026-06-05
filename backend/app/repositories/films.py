from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cycle import Cycle
from app.models.film import Film
from app.schemas.imported import ImportedFilm


@dataclass(slots=True)
class UpsertFilmResult:
    film: Film
    created: bool


class FilmRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(self, imported_film: ImportedFilm, *, cycle: Cycle | None = None) -> UpsertFilmResult:
        film = self._db.scalar(select(Film).where(Film.slug == imported_film.slug))
        created = film is None

        if film is None:
            film = Film(title=imported_film.title, slug=imported_film.slug, priority="medium")

        film.title = imported_film.title
        film.directors = imported_film.directors
        film.year = imported_film.year
        film.countries = imported_film.countries
        film.duration_minutes = imported_film.duration_minutes
        film.tagline = imported_film.tagline
        film.premiere_label = imported_film.premiere_label
        film.short_description = imported_film.short_description
        film.cast = imported_film.cast
        film.synopsis = imported_film.synopsis
        film.language = imported_film.language
        film.age_rating = imported_film.age_rating
        film.poster_url = imported_film.poster_url
        film.source_url = imported_film.source_url
        film.cycle_id = cycle.id if cycle else None

        self._db.add(film)
        self._db.flush()
        return UpsertFilmResult(film=film, created=created)
