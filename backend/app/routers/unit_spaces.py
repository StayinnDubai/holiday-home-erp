import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import UnitSpaceCreate, UnitSpaceOut, UnitSpaceUpdate
from app.services.master_data import UnitSpaceService

router = APIRouter(prefix="/unit-spaces", tags=["unit-spaces"])


@router.get("", response_model=ListResponse[UnitSpaceOut])
def list_unit_spaces(
    unit_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    rows, total = UnitSpaceService.list_page(db, params, unit_id=unit_id)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{space_id}", response_model=ItemResponse[UnitSpaceOut])
def get_unit_space(space_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitSpaceService.get(db, space_id))


@router.post("", response_model=ItemResponse[UnitSpaceOut], status_code=201)
def create_unit_space(payload: UnitSpaceCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitSpaceService.create(db, payload))


@router.patch("/{space_id}", response_model=ItemResponse[UnitSpaceOut])
def update_unit_space(space_id: uuid.UUID, payload: UnitSpaceUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=UnitSpaceService.update(db, space_id, payload))


@router.delete("/{space_id}", status_code=204)
def delete_unit_space(space_id: uuid.UUID, db: Session = Depends(get_db)):
    UnitSpaceService.soft_delete(db, space_id)
