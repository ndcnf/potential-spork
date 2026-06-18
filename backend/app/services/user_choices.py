from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.priorities import DEFAULT_FILM_PRIORITY
from app.models.film import Film
from app.models.screening import Screening


def reset_user_choices(db: Session) -> dict[str, int]:
    films = db.scalars(select(Film).where(Film.priority != DEFAULT_FILM_PRIORITY)).all()
    screenings = db.scalars(select(Screening).where(Screening.selection_status != "none")).all()

    for film in films:
        film.priority = DEFAULT_FILM_PRIORITY

    for screening in screenings:
        screening.selection_status = "none"

    db.commit()

    return {
        "films_reset": len(films),
        "screenings_reset": len(screenings),
    }
