import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.master_data import BuildingCreate, BuildingOut, BuildingUpdate
from app.services.master_data import BuildingService

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=ListResponse[BuildingOut])
def list_buildings(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = BuildingService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{building_id}", response_model=ItemResponse[BuildingOut])
def get_building(building_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingService.get(db, building_id))


@router.post("", response_model=ItemResponse[BuildingOut], status_code=201)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingService.create(db, payload))


@router.patch("/{building_id}", response_model=ItemResponse[BuildingOut])
def update_building(building_id: uuid.UUID, payload: BuildingUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=BuildingService.update(db, building_id, payload))


@router.delete("/{building_id}", status_code=204)
def delete_building(building_id: uuid.UUID, db: Session = Depends(get_db)):
    BuildingService.soft_delete(db, building_id)
