import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import BankAccountCreate, BankAccountOut, BankAccountUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import BankAccountService

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


@router.get("", response_model=ListResponse[BankAccountOut])
def list_bank_accounts(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BankAccountService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{bank_account_id}", response_model=ItemResponse[BankAccountOut])
def get_bank_account(bank_account_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountService.get(db, bank_account_id))


@router.post("", response_model=ItemResponse[BankAccountOut], status_code=201)
def create_bank_account(payload: BankAccountCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountService.create(db, payload))


@router.patch("/{bank_account_id}", response_model=ItemResponse[BankAccountOut])
def update_bank_account(bank_account_id: uuid.UUID, payload: BankAccountUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankAccountService.update(db, bank_account_id, payload))


@router.delete("/{bank_account_id}", status_code=204)
def delete_bank_account(bank_account_id: uuid.UUID, db: Session = Depends(get_db)):
    BankAccountService.soft_delete(db, bank_account_id)
