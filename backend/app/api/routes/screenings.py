from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import db_session
from app.models.screening import Screening
from app.schemas.screening import ScreeningRead, ScreeningUpdate
from app.services.screenings import screening_to_read, sync_film_screening_status


router = APIRouter(tags=["screenings"])


@router.get("/screenings", response_model=list[ScreeningRead])
def list_screenings(db: Session = Depends(db_session)) -> list[ScreeningRead]:
    screenings = db.scalars(select(Screening).options(joinedload(Screening.film), joinedload(Screening.venue))).all()
    return [screening_to_read(screening, screenings) for screening in screenings]


@router.patch("/screenings/{screening_id}", response_model=ScreeningRead)
def update_screening(screening_id: int, payload: ScreeningUpdate, db: Session = Depends(db_session)) -> ScreeningRead:
    screening = db.get(Screening, screening_id)
    if screening is None:
        raise HTTPException(status_code=404, detail="Screening not found")

    screening.selection_status = payload.selection_status
    db.add(screening)
    db.flush()
    sync_film_screening_status(db, screening)
    db.commit()
    db.refresh(screening)

    screenings = db.scalars(select(Screening).options(joinedload(Screening.film), joinedload(Screening.venue))).all()
    return screening_to_read(screening, screenings)
