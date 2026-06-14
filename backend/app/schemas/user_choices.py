from pydantic import BaseModel


class ResetUserChoicesSummary(BaseModel):
    films_reset: int
    screenings_reset: int
