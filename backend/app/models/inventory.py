"""Inventory management (doc §2.5) -- consumables and linen/amenity stock.

Confirmed (Q52): consumables are held as stock and expensed on issue, not on
purchase -- inventory sits on the balance sheet (account 1500) until issued, then
charges the unit's P&L. Confirmed split (Q267): every item carries a
`stock_tracked` flag -- stock-tracked items go through the full receipt/issue/
transfer/wastage/count ledger below; items with the flag off are meant to be
expensed directly at the point of purchase instead (that posting is Bills' job,
doc §6 -- not built here since the Bills module itself doesn't exist yet).

`InventoryMovement` is the single ledger for every stock event doc §2.5 asks for
(receipts, issues to unit/UnitSpace, transfers, wastage, stock count variance) --
one row per event, `movement_type` distinguishing them, rather than five separate
tables for what is fundamentally the same shape (item, date, quantity, location).
A stock count's variance is itself recorded as a 'count_adjustment' movement (the
variance quantity, positive or negative) rather than a separate "counted vs
expected" object -- simpler, and the audit trail already carries the "why" via
`notes`.

Location (doc §2.5: "central store, building, unit, or UnitSpace") is
`location_type` + a free-text `location_reference` rather than a fully polymorphic
FK to Building/Unit/UnitSpace -- that would need dynamic-relation-picker UI the
shared CRUD form doesn't have yet. Cheap to upgrade to real FKs later; the location
*fact* is captured now, which is what "stock by location" actually depends on.

Valuation method is weighted average [CONFIRM per doc §2.5], computed at read time
from receipt history (quantity-weighted mean of receipt unit costs) rather than a
running recalculated balance -- correct and simple, since nothing here posts to
the GL yet (no Accounting-core journal engine to keep in step with).
"""
import uuid
from datetime import date
from datetime import date as _date  # InventoryMovement has a field literally named
# `date`, which shadows the `date` type inside its own class body -- alias avoids it.

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base


class InventoryItem(AuditableRecord, Base):
    """doc §2.5 "item master" -- consumables, linen, amenities."""

    __tablename__ = "inventory_item"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit_of_measure: Mapped[str | None] = mapped_column(String(50))
    reorder_level: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    # doc §2.5 Q267: stock-tracked (full receipt/issue/transfer/count ledger) vs
    # expensed on purchase (no stock balance carried) -- set item by item, a
    # judgement call, never a price-band rule.
    stock_tracked: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[str | None] = mapped_column(String(100))
    default_supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("counterparty.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="item")


class InventoryMovement(AuditableRecord, Base):
    """doc §2.5 stock ledger -- "Stock movements are mandatory, not optional...
    this is the one place where the system depends on operational discipline
    rather than on validation." `unit_cost` and `supplier_id` are only meaningful
    for receipts (they feed the weighted-average cost calculation); left null on
    issues/transfers/wastage/counts.
    """

    __tablename__ = "inventory_movement"

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inventory_item.id"), nullable=False)
    # receipt | issue | transfer | wastage | count_adjustment
    movement_type: Mapped[str] = mapped_column(String(20))
    date: Mapped[_date] = mapped_column(Date)
    # Always positive except count_adjustment, which may be negative (a shortfall).
    quantity: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False))

    # Primary location: destination for receipts, source for issues/wastage/
    # transfers-out, the counted location for count_adjustment.
    location_type: Mapped[str] = mapped_column(String(20))  # central_store | building | unit | unit_space
    location_reference: Mapped[str | None] = mapped_column(String(255))

    # Destination, transfers only.
    to_location_type: Mapped[str | None] = mapped_column(String(20))
    to_location_reference: Mapped[str | None] = mapped_column(String(255))

    unit_cost: Mapped[float | None] = mapped_column(Numeric(12, 4, asdecimal=False))
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("counterparty.id"))
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    item: Mapped[InventoryItem] = relationship(back_populates="movements")
