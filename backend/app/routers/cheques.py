import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.accounting import ChequeCreate, ChequeOut, ChequeUpdate
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.services.accounting import ChequeService

router = APIRouter(prefix="/cheques", tags=["cheques"])


@router.get("", response_model=ListResponse[ChequeOut])
def list_cheques(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = ChequeService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{cheque_id}", response_model=ItemResponse[ChequeOut])
def get_cheque(cheque_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=ChequeService.get(db, cheque_id))


@router.post("", response_model=ItemResponse[ChequeOut], status_code=201)
def create_cheque(payload: ChequeCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=ChequeService.create(db, payload))


@router.patch("/{cheque_id}", response_model=ItemResponse[ChequeOut])
def update_cheque(cheque_id: uuid.UUID, payload: ChequeUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=ChequeService.update(db, cheque_id, payload))


@router.delete("/{cheque_id}", status_code=204)
def delete_cheque(cheque_id: uuid.UUID, db: Session = Depends(get_db)):
    ChequeService.soft_delete(db, cheque_id)
