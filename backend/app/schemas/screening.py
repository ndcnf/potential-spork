from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import SelectionStatus


class ScreeningRead(BaseModel):
    id: int
    film_id: int
    film_title: str
    venue_id: int | None
    venue_name: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    selection_status: SelectionStatus
    derived_state: str


class ScreeningUpdate(BaseModel):
    selection_status: SelectionStatus
