import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import BankStatementEntryCreate, BankStatementEntryOut, BankStatementEntryUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import BankStatementEntryService

router = APIRouter(prefix="/bank-statement-entries", tags=["bank-statement-entries"])


@router.get("", response_model=ListResponse[BankStatementEntryOut])
def list_bank_statement_entries(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
    bank_account_id: uuid.UUID | None = Query(None),
    kind: str | None = Query(None),
):
    rows, total = BankStatementEntryService.list_page(db, params, bank_account_id=bank_account_id, kind=kind)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{entry_id}", response_model=ItemResponse[BankStatementEntryOut])
def get_bank_statement_entry(entry_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementEntryService.get(db, entry_id))


@router.post("", response_model=ItemResponse[BankStatementEntryOut], status_code=201)
def create_bank_statement_entry(payload: BankStatementEntryCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementEntryService.create(db, payload))


@router.patch("/{entry_id}", response_model=ItemResponse[BankStatementEntryOut])
def update_bank_statement_entry(entry_id: uuid.UUID, payload: BankStatementEntryUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementEntryService.update(db, entry_id, payload))


@router.delete("/{entry_id}", status_code=204)
def delete_bank_statement_entry(entry_id: uuid.UUID, db: Session = Depends(get_db)):
    BankStatementEntryService.soft_delete(db, entry_id)
