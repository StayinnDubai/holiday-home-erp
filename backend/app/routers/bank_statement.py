import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import BankStatementLineCreate, BankStatementLineOut, BankStatementLineUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import BankStatementLineService

router = APIRouter(prefix="/bank-statement-lines", tags=["bank-statement"])


@router.get("", response_model=ListResponse[BankStatementLineOut])
def list_bank_statement_lines(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BankStatementLineService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{line_id}", response_model=ItemResponse[BankStatementLineOut])
def get_bank_statement_line(line_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementLineService.get(db, line_id))


@router.post("", response_model=ItemResponse[BankStatementLineOut], status_code=201)
def create_bank_statement_line(payload: BankStatementLineCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementLineService.create(db, payload))


@router.patch("/{line_id}", response_model=ItemResponse[BankStatementLineOut])
def update_bank_statement_line(line_id: uuid.UUID, payload: BankStatementLineUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BankStatementLineService.update(db, line_id, payload))


@router.delete("/{line_id}", status_code=204)
def delete_bank_statement_line(line_id: uuid.UUID, db: Session = Depends(get_db)):
    BankStatementLineService.soft_delete(db, line_id)
