import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import CounterpartyGroupCreate, CounterpartyGroupOut, CounterpartyGroupUpdate
from app.services.master_data import CounterpartyGroupService

router = APIRouter(prefix="/counterparty-groups", tags=["counterparty-groups"])


@router.get("", response_model=ListResponse[CounterpartyGroupOut])
def list_counterparty_groups(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = CounterpartyGroupService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{group_id}", response_model=ItemResponse[CounterpartyGroupOut])
def get_counterparty_group(group_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyGroupService.get(db, group_id))


@router.post("", response_model=ItemResponse[CounterpartyGroupOut], status_code=201)
def create_counterparty_group(payload: CounterpartyGroupCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyGroupService.create(db, payload))


@router.patch("/{group_id}", response_model=ItemResponse[CounterpartyGroupOut])
def update_counterparty_group(group_id: uuid.UUID, payload: CounterpartyGroupUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyGroupService.update(db, group_id, payload))


@router.delete("/{group_id}", status_code=204)
def delete_counterparty_group(group_id: uuid.UUID, db: Session = Depends(get_db)):
    CounterpartyGroupService.soft_delete(db, group_id)
