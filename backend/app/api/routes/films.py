from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import db_session
from app.models.film import Film
from app.schemas.film import FilmRead, FilmUpdate


router = APIRouter(tags=["films"])


def _to_film_read(film: Film) -> FilmRead:
    return FilmRead(
        id=film.id,
        title=film.title,
        slug=film.slug,
        directors=film.directors,
        year=film.year,
        countries=film.countries,
        duration_minutes=film.duration_minutes,
        tagline=film.tagline,
        premiere_label=film.premiere_label,
        short_description=film.short_description,
        cast=film.cast,
        synopsis=film.synopsis,
        language=film.language,
        age_rating=film.age_rating,
        poster_url=film.poster_url,
        priority=film.priority,
        planning_type=film.planning_type or "standalone",
        cycle_id=film.cycle_id,
        cycle_name=film.cycle.name if film.cycle else None,
        cycle_color=film.cycle.color if film.cycle else None,
    )


@router.get("/films", response_model=list[FilmRead])
def list_films(
    db: Session = Depends(db_session),
    q: str | None = Query(default=None),
    cycle_id: int | None = Query(default=None),
    priority: str | None = Query(default=None),
) -> list[FilmRead]:
    query = select(Film).options(joinedload(Film.cycle)).order_by(Film.title)

    if q:
        search = f"%{q}%"
        query = query.where(
            or_(Film.title.ilike(search), Film.directors.ilike(search), Film.cast.ilike(search))
        )
    if cycle_id is not None:
        query = query.where(Film.cycle_id == cycle_id)
    if priority is not None:
        query = query.where(Film.priority == priority)

    films = db.scalars(query).unique().all()
    return [_to_film_read(film) for film in films]


@router.patch("/films/{film_id}", response_model=FilmRead)
def update_film(film_id: int, payload: FilmUpdate, db: Session = Depends(db_session)) -> FilmRead:
    film = db.get(Film, film_id)
    if film is None:
        raise HTTPException(status_code=404, detail="Film not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(film, field, value)

    db.add(film)
    db.commit()
    db.refresh(film)
    return _to_film_read(film)
