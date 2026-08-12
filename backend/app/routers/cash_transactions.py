import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import CashTransactionCreate, CashTransactionOut, CashTransactionUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import CashTransactionService

router = APIRouter(prefix="/cash-transactions", tags=["cash-transactions"])


@router.get("", response_model=ListResponse[CashTransactionOut])
def list_cash_transactions(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = CashTransactionService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{txn_id}", response_model=ItemResponse[CashTransactionOut])
def get_cash_transaction(txn_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=CashTransactionService.get(db, txn_id))


@router.post("", response_model=ItemResponse[CashTransactionOut], status_code=201)
def create_cash_transaction(payload: CashTransactionCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=CashTransactionService.create(db, payload))


@router.patch("/{txn_id}", response_model=ItemResponse[CashTransactionOut])
def update_cash_transaction(txn_id: uuid.UUID, payload: CashTransactionUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=CashTransactionService.update(db, txn_id, payload))


@router.delete("/{txn_id}", status_code=204)
def delete_cash_transaction(txn_id: uuid.UUID, db: Session = Depends(get_db)):
    CashTransactionService.soft_delete(db, txn_id)
