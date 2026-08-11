import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.inventory import InventoryItemCreate, InventoryItemOut, InventoryItemUpdate
from app.services.inventory import InventoryItemService

router = APIRouter(prefix="/inventory-items", tags=["inventory-items"])


@router.get("", response_model=ListResponse[InventoryItemOut])
def list_inventory_items(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = InventoryItemService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{item_id}", response_model=ItemResponse[InventoryItemOut])
def get_inventory_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryItemService.get(db, item_id))


@router.post("", response_model=ItemResponse[InventoryItemOut], status_code=201)
def create_inventory_item(payload: InventoryItemCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryItemService.create(db, payload))


@router.patch("/{item_id}", response_model=ItemResponse[InventoryItemOut])
def update_inventory_item(item_id: uuid.UUID, payload: InventoryItemUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=InventoryItemService.update(db, item_id, payload))


@router.delete("/{item_id}", status_code=204)
def delete_inventory_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    InventoryItemService.soft_delete(db, item_id)
