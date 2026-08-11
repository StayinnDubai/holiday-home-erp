import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.inventory import InventoryMovementCreate, InventoryMovementOut, InventoryMovementUpdate
from app.services.inventory import InventoryMovementService

router = APIRouter(prefix="/inventory-movements", tags=["inventory-movements"])


@router.get("", response_model=ListResponse[InventoryMovementOut])
def list_inventory_movements(
    item_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    rows, total = InventoryMovementService.list_page(db, params, item_id=item_id)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{movement_id}", response_model=ItemResponse[InventoryMovementOut])
def get_inventory_movement(movement_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryMovementService.get(db, movement_id))


@router.post("", response_model=ItemResponse[InventoryMovementOut], status_code=201)
def create_inventory_movement(payload: InventoryMovementCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryMovementService.create(db, payload))


@router.patch("/{movement_id}", response_model=ItemResponse[InventoryMovementOut])
def update_inventory_movement(movement_id: uuid.UUID, payload: InventoryMovementUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryMovementService.update(db, movement_id, payload))


@router.delete("/{movement_id}", status_code=204)
def delete_inventory_movement(movement_id: uuid.UUID, db: Session = Depends(get_db)):
    InventoryMovementService.soft_delete(db, movement_id)
