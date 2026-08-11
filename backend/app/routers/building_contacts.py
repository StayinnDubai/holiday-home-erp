import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import BuildingContactCreate, BuildingContactOut, BuildingContactUpdate
from app.services.master_data import BuildingContactService

router = APIRouter(prefix="/building-contacts", tags=["building-contacts"])


@router.get("", response_model=ListResponse[BuildingContactOut])
def list_building_contacts(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BuildingContactService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{contact_id}", response_model=ItemResponse[BuildingContactOut])
def get_building_contact(contact_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingContactService.get(db, contact_id))


@router.post("", response_model=ItemResponse[BuildingContactOut], status_code=201)
def create_building_contact(payload: BuildingContactCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingContactService.create(db, payload))


@router.patch("/{contact_id}", response_model=ItemResponse[BuildingContactOut])
def update_building_contact(contact_id: uuid.UUID, payload: BuildingContactUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingContactService.update(db, contact_id, payload))


@router.delete("/{contact_id}", status_code=204)
def delete_building_contact(contact_id: uuid.UUID, db: Session = Depends(get_db)):
    BuildingContactService.soft_delete(db, contact_id)
