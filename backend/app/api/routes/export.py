from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import db_session
from app.models.screening import Screening
from app.services.export_ics import build_calendar


router = APIRouter(tags=["export"])


@router.get("/exports/confirmed.ics")
def export_confirmed_ics(db: Session = Depends(db_session)) -> Response:
    screenings = db.scalars(
        select(Screening)
        .options(joinedload(Screening.film), joinedload(Screening.venue))
        .where(Screening.selection_status == "confirmed")
    ).all()

    calendar_bytes = build_calendar(screenings)
    return Response(
        content=calendar_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="potential-spork-confirmed.ics"'},
    )
