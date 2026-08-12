import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import BillCreate, BillOut, BillUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import BillService

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("", response_model=ListResponse[BillOut])
def list_bills(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BillService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{bill_id}", response_model=ItemResponse[BillOut])
def get_bill(bill_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BillService.get(db, bill_id))


@router.post("", response_model=ItemResponse[BillOut], status_code=201)
def create_bill(payload: BillCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BillService.create(db, payload))


@router.patch("/{bill_id}", response_model=ItemResponse[BillOut])
def update_bill(bill_id: uuid.UUID, payload: BillUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BillService.update(db, bill_id, payload))


@router.delete("/{bill_id}", status_code=204)
def delete_bill(bill_id: uuid.UUID, db: Session = Depends(get_db)):
    BillService.soft_delete(db, bill_id)
