from datetime import datetime

from app.models.screening import Screening
from app.schemas.screening import ScreeningRead


def screenings_overlap(left: Screening, right: Screening) -> bool:
    if left.id == right.id or left.starts_at is None or left.ends_at is None or right.starts_at is None or right.ends_at is None:
        return False
    return left.starts_at < right.ends_at and right.starts_at < left.ends_at


def derive_screening_state(screening: Screening, all_screenings: list[Screening]) -> str:
    if screening.starts_at is not None and screening.starts_at < datetime.now(screening.starts_at.tzinfo):
        return "past"

    if screening.selection_status in {"tentative", "confirmed"}:
        return "selected"

    if any(
        other.film_id == screening.film_id and other.id != screening.id and other.selection_status in {"tentative", "confirmed"}
        for other in all_screenings
    ):
        return "disabled"

    if any(
        other.selection_status in {"tentative", "confirmed"} and screenings_overlap(screening, other)
        for other in all_screenings
    ):
        return "conflict"

    return "available"


def screening_to_read(screening: Screening, all_screenings: list[Screening]) -> ScreeningRead:
    return ScreeningRead(
        id=screening.id,
        film_id=screening.film_id,
        film_title=screening.film.title,
        venue_id=screening.venue_id,
        venue_name=screening.venue.name if screening.venue else None,
        starts_at=screening.starts_at,
        ends_at=screening.ends_at,
        selection_status=screening.selection_status,
        derived_state=derive_screening_state(screening, all_screenings),
    )


def sync_film_screening_status(db, screening: Screening) -> None:
    if screening.selection_status != "confirmed":
        return

    siblings = db.query(Screening).filter(Screening.film_id == screening.film_id, Screening.id != screening.id).all()
    for sibling in siblings:
        if sibling.selection_status != "rejected":
            sibling.selection_status = "none"
            db.add(sibling)
