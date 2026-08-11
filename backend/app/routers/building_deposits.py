import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import BuildingDepositCreate, BuildingDepositOut, BuildingDepositUpdate
from app.services.master_data import BuildingDepositService

router = APIRouter(prefix="/building-deposits", tags=["building-deposits"])


@router.get("", response_model=ListResponse[BuildingDepositOut])
def list_building_deposits(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BuildingDepositService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{deposit_id}", response_model=ItemResponse[BuildingDepositOut])
def get_building_deposit(deposit_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingDepositService.get(db, deposit_id))


@router.post("", response_model=ItemResponse[BuildingDepositOut], status_code=201)
def create_building_deposit(payload: BuildingDepositCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingDepositService.create(db, payload))


@router.patch("/{deposit_id}", response_model=ItemResponse[BuildingDepositOut])
def update_building_deposit(deposit_id: uuid.UUID, payload: BuildingDepositUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingDepositService.update(db, deposit_id, payload))


@router.delete("/{deposit_id}", status_code=204)
def delete_building_deposit(deposit_id: uuid.UUID, db: Session = Depends(get_db)):
    BuildingDepositService.soft_delete(db, deposit_id)
