import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import InvoiceCreate, InvoiceOut, InvoiceUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=ListResponse[InvoiceOut])
def list_invoices(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = InvoiceService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{invoice_id}", response_model=ItemResponse[InvoiceOut])
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=InvoiceService.get(db, invoice_id))


@router.post("", response_model=ItemResponse[InvoiceOut], status_code=201)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=InvoiceService.create(db, payload))


@router.patch("/{invoice_id}", response_model=ItemResponse[InvoiceOut])
def update_invoice(invoice_id: uuid.UUID, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=InvoiceService.update(db, invoice_id, payload))


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db)):
    InvoiceService.soft_delete(db, invoice_id)
