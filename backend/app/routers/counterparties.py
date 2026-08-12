import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import CounterpartyCreate, CounterpartyOut, CounterpartyUpdate
from app.services.master_data import CounterpartyService

router = APIRouter(prefix="/counterparties", tags=["counterparties"])


@router.get("", response_model=ListResponse[CounterpartyOut])
def list_counterparties(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
    landlord_only: bool = Query(False),
):
    rows, total = CounterpartyService.list_page(db, params, landlord_only=landlord_only)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{counterparty_id}", response_model=ItemResponse[CounterpartyOut])
def get_counterparty(counterparty_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyService.get(db, counterparty_id))


@router.post("", response_model=ItemResponse[CounterpartyOut], status_code=201)
def create_counterparty(payload: CounterpartyCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyService.create(db, payload))


@router.patch("/{counterparty_id}", response_model=ItemResponse[CounterpartyOut])
def update_counterparty(counterparty_id: uuid.UUID, payload: CounterpartyUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CounterpartyService.update(db, counterparty_id, payload))


@router.delete("/{counterparty_id}", status_code=204)
def delete_counterparty(counterparty_id: uuid.UUID, db: Session = Depends(get_db)):
    CounterpartyService.soft_delete(db, counterparty_id)
