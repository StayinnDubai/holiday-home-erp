import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.leasing import (
    TenancyContractAdjustmentCreate,
    TenancyContractAdjustmentOut,
    TenancyContractAdjustmentUpdate,
)
from app.services.leasing import TenancyContractAdjustmentService

router = APIRouter(prefix="/tenancy-contract-adjustments", tags=["tenancy-contract-adjustments"])


@router.get("", response_model=ListResponse[TenancyContractAdjustmentOut])
def list_adjustments(
    contract_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    rows, total = TenancyContractAdjustmentService.list_page(db, params, contract_id=contract_id)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{adjustment_id}", response_model=ItemResponse[TenancyContractAdjustmentOut])
def get_adjustment(adjustment_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractAdjustmentService.get(db, adjustment_id))


@router.post("", response_model=ItemResponse[TenancyContractAdjustmentOut], status_code=201)
def create_adjustment(payload: TenancyContractAdjustmentCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractAdjustmentService.create(db, payload))


@router.patch("/{adjustment_id}", response_model=ItemResponse[TenancyContractAdjustmentOut])
def update_adjustment(adjustment_id: uuid.UUID, payload: TenancyContractAdjustmentUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractAdjustmentService.update(db, adjustment_id, payload))


@router.delete("/{adjustment_id}", status_code=204)
def delete_adjustment(adjustment_id: uuid.UUID, db: Session = Depends(get_db)):
    TenancyContractAdjustmentService.soft_delete(db, adjustment_id)
