from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.user_choices import ResetUserChoicesSummary
from app.services.user_choices import reset_user_choices


router = APIRouter(tags=["user choices"])


@router.post("/user-choices/reset", response_model=ResetUserChoicesSummary)
def reset_choices(db: Session = Depends(db_session)) -> ResetUserChoicesSummary:
    return ResetUserChoicesSummary(**reset_user_choices(db))
