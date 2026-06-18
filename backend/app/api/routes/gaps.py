from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import db_session
from app.core.priorities import PLANNING_FILM_PRIORITIES
from app.models.film import Film
from app.schemas.planning import GapSuggestion


router = APIRouter(tags=["gaps"])


@router.get("/gaps", response_model=list[GapSuggestion])
def get_gap_suggestions(db: Session = Depends(db_session)) -> list[GapSuggestion]:
    # Placeholder V1: surface medium+ films with no scheduling data yet,
    # so the frontend can already drive the pre-selection workflow.
    films = db.scalars(
        select(Film).options(joinedload(Film.cycle)).where(Film.priority.in_(PLANNING_FILM_PRIORITIES)).order_by(Film.title)
    ).all()

    if not films:
        return []

    return [GapSuggestion(gap_label="No screenings imported yet", screenings=[])]
