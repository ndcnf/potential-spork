from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.imports import ImportCatalogPayload, ImportSummary
from app.services.import_nifff import import_nifff_catalog


router = APIRouter(tags=["imports"])


@router.post("/imports/nifff/catalog", response_model=ImportSummary)
def import_catalog(payload: ImportCatalogPayload, db: Session = Depends(db_session)) -> ImportSummary:
    return import_nifff_catalog(db=db, year=payload.year, schedule_url=str(payload.schedule_url) if payload.schedule_url else None)
