import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.leasing import EjariRegistrationCreate, EjariRegistrationOut, EjariRegistrationUpdate
from app.services.leasing import EjariRegistrationService

router = APIRouter(prefix="/ejari-registrations", tags=["ejari-registrations"])


@router.get("", response_model=ListResponse[EjariRegistrationOut])
def list_ejari_registrations(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = EjariRegistrationService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{ejari_id}", response_model=ItemResponse[EjariRegistrationOut])
def get_ejari_registration(ejari_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=EjariRegistrationService.get(db, ejari_id))


@router.post("", response_model=ItemResponse[EjariRegistrationOut], status_code=201)
def create_ejari_registration(payload: EjariRegistrationCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=EjariRegistrationService.create(db, payload))


@router.patch("/{ejari_id}", response_model=ItemResponse[EjariRegistrationOut])
def update_ejari_registration(ejari_id: uuid.UUID, payload: EjariRegistrationUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=EjariRegistrationService.update(db, ejari_id, payload))


@router.delete("/{ejari_id}", status_code=204)
def delete_ejari_registration(ejari_id: uuid.UUID, db: Session = Depends(get_db)):
    EjariRegistrationService.soft_delete(db, ejari_id)
