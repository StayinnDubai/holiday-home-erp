import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import JournalEntryCreate, JournalEntryOut, JournalEntryUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import JournalEntryService

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])


@router.get("", response_model=ListResponse[JournalEntryOut])
def list_journal_entries(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = JournalEntryService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{entry_id}", response_model=ItemResponse[JournalEntryOut])
def get_journal_entry(entry_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=JournalEntryService.get(db, entry_id))


@router.post("", response_model=ItemResponse[JournalEntryOut], status_code=201)
def create_journal_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=JournalEntryService.create(db, payload))


@router.patch("/{entry_id}", response_model=ItemResponse[JournalEntryOut])
def update_journal_entry(entry_id: uuid.UUID, payload: JournalEntryUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=JournalEntryService.update(db, entry_id, payload))


@router.delete("/{entry_id}", status_code=204)
def delete_journal_entry(entry_id: uuid.UUID, db: Session = Depends(get_db)):
    JournalEntryService.soft_delete(db, entry_id)
