import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import CostTypeCreate, CostTypeOut, CostTypeUpdate
from app.services.foundation import CostTypeService

router = APIRouter(prefix="/cost-types", tags=["cost-types"])


@router.get("", response_model=ListResponse[CostTypeOut])
def list_cost_types(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = CostTypeService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{cost_type_id}", response_model=ItemResponse[CostTypeOut])
def get_cost_type(cost_type_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=CostTypeService.get(db, cost_type_id))


@router.post("", response_model=ItemResponse[CostTypeOut], status_code=201)
def create_cost_type(payload: CostTypeCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=CostTypeService.create(db, payload))


@router.patch("/{cost_type_id}", response_model=ItemResponse[CostTypeOut])
def update_cost_type(cost_type_id: uuid.UUID, payload: CostTypeUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CostTypeService.update(db, cost_type_id, payload))


@router.delete("/{cost_type_id}", status_code=204)
def delete_cost_type(cost_type_id: uuid.UUID, db: Session = Depends(get_db)):
    CostTypeService.soft_delete(db, cost_type_id)
