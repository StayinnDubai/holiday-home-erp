from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.warnings import WarningsOut
from app.services.warnings import WarningsService

router = APIRouter(prefix="/warnings", tags=["warnings"])


@router.get("", response_model=WarningsOut)
def get_warnings(db: Session = Depends(get_db)):
    return WarningsService.get_warnings(db)
