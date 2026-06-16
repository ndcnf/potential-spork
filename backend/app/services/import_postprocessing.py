from __future__ import annotations

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.film import Film
from app.sources.nifff_html.normalizer import category_tokens


def is_package_url(source_url: str | None) -> bool:
    return source_url is not None and "/film-package/" in source_url


def sync_existing_package_member_planning_types(db: Session) -> None:
    films = db.query(Film).options(joinedload(Film.cycle), selectinload(Film.screenings)).all()
    package_cycle_tokens = set().union(
        *(
            category_tokens(film.cycle.name if film.cycle else None)
            for film in films
            if film.planning_type == "package" or is_package_url(film.source_url)
        )
    )

    if not package_cycle_tokens:
        return

    for film in films:
        if film.planning_type == "package" or is_package_url(film.source_url):
            film.planning_type = "package"
            continue

        if not film.screenings and category_tokens(film.cycle.name if film.cycle else None).intersection(package_cycle_tokens):
            film.planning_type = "package_member"
            continue

        if film.planning_type == "package_member":
            film.planning_type = "standalone"
