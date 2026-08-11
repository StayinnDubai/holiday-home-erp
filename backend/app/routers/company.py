from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.common import ItemResponse
from app.schemas.foundation import EntityOut, EntityUpdate
from app.services.company import CompanyService

router = APIRouter(prefix="/company", tags=["company"])


@router.get("", response_model=ItemResponse[EntityOut])
def get_company(db: Session = Depends(get_db)):
    return ItemResponse(data=CompanyService.get(db))


@router.patch("", response_model=ItemResponse[EntityOut])
def update_company(payload: EntityUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CompanyService.update(db, payload))
