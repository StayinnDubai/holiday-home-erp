from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.models.foundation import Setting
from app.schemas.common import ItemResponse, ListResponse, ListMeta
from app.schemas.foundation import SettingCreate, SettingOut, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=ListResponse[SettingOut])
def list_settings(db: Session = Depends(get_db)):
    rows = list(db.scalars(select(Setting).order_by(Setting.key)).all())
    return ListResponse(data=rows, meta=ListMeta(page=1, page_size=len(rows) or 1, total=len(rows)))


@router.get("/{key}", response_model=ItemResponse[SettingOut])
def get_setting(key: str, db: Session = Depends(get_db)):
    row = db.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none()
    if row is None:
        raise ApiError(f"Setting '{key}' not found.", code="not_found", status_code=404)
    return ItemResponse(data=row)


@router.post("", response_model=ItemResponse[SettingOut], status_code=201)
def create_setting(payload: SettingCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(Setting).where(Setting.key == payload.key)).scalar_one_or_none()
    if existing is not None:
        raise ApiError(f"Setting '{payload.key}' already exists.", code="conflict", status_code=409)
    row = Setting(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ItemResponse(data=row)


@router.patch("/{key}", response_model=ItemResponse[SettingOut])
def update_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db)):
    row = db.execute(select(Setting).where(Setting.key == key)).scalar_one_or_none()
    if row is None:
        raise ApiError(f"Setting '{key}' not found.", code="not_found", status_code=404)
    row.value = payload.value
    db.commit()
    db.refresh(row)
    return ItemResponse(data=row)
