import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.online_accounts import OnlineAccountCreate, OnlineAccountOut, OnlineAccountUpdate
from app.services.online_accounts import OnlineAccountService

router = APIRouter(prefix="/online-accounts", tags=["online-accounts"])


@router.get("", response_model=ListResponse[OnlineAccountOut])
def list_online_accounts(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = OnlineAccountService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{account_id}", response_model=ItemResponse[OnlineAccountOut])
def get_online_account(account_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=OnlineAccountService.get(db, account_id))


@router.post("", response_model=ItemResponse[OnlineAccountOut], status_code=201)
def create_online_account(payload: OnlineAccountCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=OnlineAccountService.create(db, payload))


@router.patch("/{account_id}", response_model=ItemResponse[OnlineAccountOut])
def update_online_account(account_id: uuid.UUID, payload: OnlineAccountUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=OnlineAccountService.update(db, account_id, payload))


@router.delete("/{account_id}", status_code=204)
def delete_online_account(account_id: uuid.UUID, db: Session = Depends(get_db)):
    OnlineAccountService.soft_delete(db, account_id)
