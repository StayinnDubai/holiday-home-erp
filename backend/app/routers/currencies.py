import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import CurrencyCreate, CurrencyOut, CurrencyUpdate
from app.services.foundation import CurrencyService

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("", response_model=ListResponse[CurrencyOut])
def list_currencies(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = CurrencyService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{currency_id}", response_model=ItemResponse[CurrencyOut])
def get_currency(currency_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=CurrencyService.get(db, currency_id))


@router.post("", response_model=ItemResponse[CurrencyOut], status_code=201)
def create_currency(payload: CurrencyCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=CurrencyService.create(db, payload))


@router.patch("/{currency_id}", response_model=ItemResponse[CurrencyOut])
def update_currency(currency_id: uuid.UUID, payload: CurrencyUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CurrencyService.update(db, currency_id, payload))


@router.delete("/{currency_id}", status_code=204)
def delete_currency(currency_id: uuid.UUID, db: Session = Depends(get_db)):
    CurrencyService.soft_delete(db, currency_id)
