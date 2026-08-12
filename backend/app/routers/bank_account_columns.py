import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import BankAccountColumnCreate, BankAccountColumnOut, BankAccountColumnUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import BankAccountColumnService

router = APIRouter(prefix="/bank-account-columns", tags=["bank-account-columns"])


@router.get("", response_model=ListResponse[BankAccountColumnOut])
def list_bank_account_columns(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
    bank_account_id: uuid.UUID | None = Query(None),
    applies_to: str | None = Query(None),
):
    rows, total = BankAccountColumnService.list_page(db, params, bank_account_id=bank_account_id, applies_to=applies_to)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{column_id}", response_model=ItemResponse[BankAccountColumnOut])
def get_bank_account_column(column_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountColumnService.get(db, column_id))


@router.post("", response_model=ItemResponse[BankAccountColumnOut], status_code=201)
def create_bank_account_column(payload: BankAccountColumnCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountColumnService.create(db, payload))


@router.patch("/{column_id}", response_model=ItemResponse[BankAccountColumnOut])
def update_bank_account_column(column_id: uuid.UUID, payload: BankAccountColumnUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountColumnService.update(db, column_id, payload))


@router.delete("/{column_id}", status_code=204)
def delete_bank_account_column(column_id: uuid.UUID, db: Session = Depends(get_db)):
    BankAccountColumnService.soft_delete(db, column_id)
