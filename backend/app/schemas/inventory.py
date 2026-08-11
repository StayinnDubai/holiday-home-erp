import uuid
from datetime import date as _date  # InventoryMovement has a field literally named
# `date`, which shadows the `date` type inside its own class body -- alias avoids it.

from pydantic import BaseModel, ConfigDict


# ---------- Inventory item (item master, doc §2.5) ----------
class InventoryItemBase(BaseModel):
    code: str
    name: str
    unit_of_measure: str | None = None
    reorder_level: float | None = None
    stock_tracked: bool = True
    category: str | None = None
    default_supplier_id: uuid.UUID | None = None
    notes: str | None = None
    active: bool = True


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    unit_of_measure: str | None = None
    reorder_level: float | None = None
    stock_tracked: bool | None = None
    category: str | None = None
    default_supplier_id: uuid.UUID | None = None
    notes: str | None = None
    active: bool | None = None


class InventoryItemOut(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    default_supplier_name: str | None = None
    # Computed from InventoryMovement history (doc §2.5) -- weighted average
    # [CONFIRM], quantity-weighted mean of receipt unit costs.
    quantity_on_hand: float = 0
    weighted_average_cost: float | None = None
    total_value: float | None = None


# ---------- Inventory movement (receipt | issue | transfer | wastage | count_adjustment) ----------
class InventoryMovementBase(BaseModel):
    item_id: uuid.UUID
    movement_type: str  # receipt | issue | transfer | wastage | count_adjustment
    date: _date
    quantity: float
    location_type: str  # central_store | building | unit | unit_space
    location_reference: str | None = None
    to_location_type: str | None = None  # transfers only
    to_location_reference: str | None = None
    unit_cost: float | None = None  # receipts only -- feeds weighted-average cost
    supplier_id: uuid.UUID | None = None  # receipts only
    reference: str | None = None
    notes: str | None = None


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovementUpdate(BaseModel):
    item_id: uuid.UUID | None = None
    movement_type: str | None = None
    date: _date | None = None
    quantity: float | None = None
    location_type: str | None = None
    location_reference: str | None = None
    to_location_type: str | None = None
    to_location_reference: str | None = None
    unit_cost: float | None = None
    supplier_id: uuid.UUID | None = None
    reference: str | None = None
    notes: str | None = None


class InventoryMovementOut(InventoryMovementBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_code: str | None = None
    item_name: str | None = None
    supplier_name: str | None = None
