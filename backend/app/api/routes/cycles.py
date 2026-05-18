from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.cycle import Cycle
from app.schemas.cycle import CycleRead, CycleUpdate


router = APIRouter(tags=["cycles"])


@router.get("/cycles", response_model=list[CycleRead])
def list_cycles(db: Session = Depends(db_session)) -> list[Cycle]:
    return db.scalars(select(Cycle).order_by(Cycle.name)).all()


@router.patch("/cycles/{cycle_id}", response_model=CycleRead)
def update_cycle(cycle_id: int, payload: CycleUpdate, db: Session = Depends(db_session)) -> Cycle:
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Cycle not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(cycle, field, value)

    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle
