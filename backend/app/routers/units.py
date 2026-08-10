import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import UnitCreate, UnitOut, UnitUpdate
from app.services.master_data import UnitService

router = APIRouter(prefix="/units", tags=["units"])


@router.get("", response_model=ListResponse[UnitOut])
def list_units(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = UnitService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{unit_id}", response_model=ItemResponse[UnitOut])
def get_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitService.get(db, unit_id))


@router.post("", response_model=ItemResponse[UnitOut], status_code=201)
def create_unit(payload: UnitCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitService.create(db, payload))


@router.patch("/{unit_id}", response_model=ItemResponse[UnitOut])
def update_unit(unit_id: uuid.UUID, payload: UnitUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitService.update(db, unit_id, payload))


@router.delete("/{unit_id}", status_code=204)
def delete_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    UnitService.soft_delete(db, unit_id)
