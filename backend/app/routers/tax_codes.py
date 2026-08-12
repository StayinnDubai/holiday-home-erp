import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import TaxCodeCreate, TaxCodeOut, TaxCodeUpdate
from app.services.foundation import TaxCodeService

router = APIRouter(prefix="/tax-codes", tags=["tax-codes"])


@router.get("", response_model=ListResponse[TaxCodeOut])
def list_tax_codes(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = TaxCodeService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{tax_code_id}", response_model=ItemResponse[TaxCodeOut])
def get_tax_code(tax_code_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=TaxCodeService.get(db, tax_code_id))


@router.post("", response_model=ItemResponse[TaxCodeOut], status_code=201)
def create_tax_code(payload: TaxCodeCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=TaxCodeService.create(db, payload))


@router.patch("/{tax_code_id}", response_model=ItemResponse[TaxCodeOut])
def update_tax_code(tax_code_id: uuid.UUID, payload: TaxCodeUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=TaxCodeService.update(db, tax_code_id, payload))


@router.delete("/{tax_code_id}", status_code=204)
def delete_tax_code(tax_code_id: uuid.UUID, db: Session = Depends(get_db)):
    TaxCodeService.soft_delete(db, tax_code_id)
