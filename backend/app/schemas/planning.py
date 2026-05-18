from pydantic import BaseModel

from app.schemas.screening import ScreeningRead


class PlanningDay(BaseModel):
    date: str
    screenings: list[ScreeningRead]


class GapSuggestion(BaseModel):
    gap_label: str
    screenings: list[ScreeningRead]
