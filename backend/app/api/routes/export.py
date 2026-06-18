from fastapi import APIRouter, Depends, Response
from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.services.export_ics import build_calendar


router = APIRouter(tags=["export"])


@router.get("/exports/confirmed.ics")
def export_confirmed_ics(db: Session = Depends(db_session)) -> Response:
    screenings = db.execute(
        text(
            """
            SELECT
                screenings.id,
                screenings.starts_at,
                screenings.ends_at,
                films.title AS film_title,
                films.tagline AS film_tagline,
                films.duration_minutes AS film_duration_minutes,
                venues.name AS venue_name
            FROM screenings
            JOIN films ON films.id = screenings.film_id
            LEFT JOIN venues ON venues.id = screenings.venue_id
            WHERE screenings.selection_status = 'confirmed'
            ORDER BY screenings.starts_at
            """
        ).columns(
            id=Integer(),
            starts_at=DateTime(),
            ends_at=DateTime(),
            film_title=String(),
            film_tagline=String(),
            film_duration_minutes=Integer(),
            venue_name=String(),
        )
    ).mappings().all()

    calendar_bytes = build_calendar(screenings)
    return Response(
        content=calendar_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="potential-spork-confirmed.ics"'},
    )
