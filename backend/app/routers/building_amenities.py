import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import BuildingAmenityCreate, BuildingAmenityOut, BuildingAmenityUpdate
from app.services.master_data import BuildingAmenityService

router = APIRouter(prefix="/building-amenities", tags=["building-amenities"])


@router.get("", response_model=ListResponse[BuildingAmenityOut])
def list_building_amenities(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BuildingAmenityService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{amenity_id}", response_model=ItemResponse[BuildingAmenityOut])
def get_building_amenity(amenity_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingAmenityService.get(db, amenity_id))


@router.post("", response_model=ItemResponse[BuildingAmenityOut], status_code=201)
def create_building_amenity(payload: BuildingAmenityCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingAmenityService.create(db, payload))


@router.patch("/{amenity_id}", response_model=ItemResponse[BuildingAmenityOut])
def update_building_amenity(amenity_id: uuid.UUID, payload: BuildingAmenityUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingAmenityService.update(db, amenity_id, payload))


@router.delete("/{amenity_id}", status_code=204)
def delete_building_amenity(amenity_id: uuid.UUID, db: Session = Depends(get_db)):
    BuildingAmenityService.soft_delete(db, amenity_id)
