import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.imports import ImportCatalogPayload, ImportSummary
from app.services.import_nifff import import_nifff_catalog_from_archive, import_nifff_catalog_from_live


router = APIRouter(tags=["imports"])


@router.post("/imports/nifff/catalog", response_model=ImportSummary)
def import_catalog(payload: ImportCatalogPayload, db: Session = Depends(db_session)) -> ImportSummary:
    schedule_url = str(payload.schedule_url) if payload.schedule_url else None
    try:
        if payload.source_mode == "prod":
            return import_nifff_catalog_from_live(db=db, year=payload.year, schedule_url=schedule_url)
        return import_nifff_catalog_from_archive(db=db, year=payload.year, schedule_url=schedule_url)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Source NIFFF indisponible: {exc}") from exc
