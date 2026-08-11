import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import AccountCreate, AccountOut, AccountUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=ListResponse[AccountOut])
def list_accounts(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = AccountService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{account_id}", response_model=ItemResponse[AccountOut])
def get_account(account_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=AccountService.get(db, account_id))


@router.post("", response_model=ItemResponse[AccountOut], status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=AccountService.create(db, payload))


@router.patch("/{account_id}", response_model=ItemResponse[AccountOut])
def update_account(account_id: uuid.UUID, payload: AccountUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=AccountService.update(db, account_id, payload))


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: uuid.UUID, db: Session = Depends(get_db)):
    AccountService.soft_delete(db, account_id)
