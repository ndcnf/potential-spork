from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import db_session
from app.models.screening import Screening
from app.schemas.planning import PlanningDay
from app.services.screenings import screening_to_read


router = APIRouter(tags=["planning"])


@router.get("/planning", response_model=list[PlanningDay])
def get_planning(db: Session = Depends(db_session)) -> list[PlanningDay]:
    screenings = db.scalars(select(Screening).options(joinedload(Screening.film), joinedload(Screening.venue))).all()
    grouped: dict[str, list] = defaultdict(list)

    for screening in screenings:
        if screening.starts_at is None:
            continue
        grouped[screening.starts_at.date().isoformat()].append(screening_to_read(screening, screenings))

    return [PlanningDay(date=date, screenings=items) for date, items in sorted(grouped.items())]
