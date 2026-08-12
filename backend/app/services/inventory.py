import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.inventory import InventoryItem, InventoryMovement
from app.models.master_data import Counterparty
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryMovementCreate,
    InventoryMovementUpdate,
)
from app.services.audit import AuditService

MOVEMENT_TYPES = ("receipt", "issue", "transfer", "wastage", "count_adjustment")
LOCATION_TYPES = ("central_store", "building", "unit", "unit_space")


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


class InventoryItemService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[InventoryItem], int]:
        stmt = select(InventoryItem).where(InventoryItem.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(InventoryItem.name.ilike(f"%{params.q}%") | InventoryItem.code.ilike(f"%{params.q}%"))
        needs_supplier_join = params.sort_by == "default_supplier_name" or "default_supplier_name" in (
            params.filter_model or {}
        )
        if needs_supplier_join:
            stmt = stmt.outerjoin(Counterparty, Counterparty.id == InventoryItem.default_supplier_id)
        stmt = apply_filters(
            stmt,
            InventoryItem,
            params.filter_model,
            extra_columns={"default_supplier_name": Counterparty.name} if needs_supplier_join else None,
        )
        if params.sort_by == "default_supplier_name":
            col = Counterparty.name
        else:
            col = _sort_col(InventoryItem, params.sort_by, InventoryItem.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        InventoryItemService._attach_computed(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, item_id: uuid.UUID) -> InventoryItem:
        row = db.get(InventoryItem, item_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory item not found.", code="not_found", status_code=404)
        InventoryItemService._attach_computed(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: InventoryItemCreate) -> InventoryItem:
        InventoryItemService._validate_unique_code(db, payload.code)
        if payload.default_supplier_id is not None:
            InventoryItemService._validate_supplier(db, payload.default_supplier_id)
        row = InventoryItem(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="inventory_item", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        InventoryItemService._attach_computed(db, [row])
        return row

    @staticmethod
    def update(db: Session, item_id: uuid.UUID, payload: InventoryItemUpdate) -> InventoryItem:
        row = db.get(InventoryItem, item_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory item not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            InventoryItemService._validate_unique_code(db, data["code"])
        if data.get("default_supplier_id") is not None:
            InventoryItemService._validate_supplier(db, data["default_supplier_id"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="inventory_item", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        InventoryItemService._attach_computed(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, item_id: uuid.UUID) -> None:
        row = db.get(InventoryItem, item_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory item not found.", code="not_found", status_code=404)
        in_use = db.scalar(
            select(func.count()).select_from(InventoryMovement)
            .where(InventoryMovement.item_id == item_id, InventoryMovement.is_deleted.is_(False))
        )
        if in_use:
            raise ApiError("Cannot delete an item with stock movements recorded against it.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="inventory_item", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(InventoryItem.id).where(InventoryItem.code == code, InventoryItem.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Item code '{code}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _validate_supplier(db: Session, supplier_id: uuid.UUID) -> None:
        supplier = db.get(Counterparty, supplier_id)
        if supplier is None or supplier.is_deleted:
            raise ApiError("Selected supplier does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_computed(db: Session, rows: list[InventoryItem]) -> None:
        """doc §2.5: valuation method weighted average [CONFIRM], applied on every
        receipt. Computed at read time as the quantity-weighted mean of receipt unit
        costs, rather than a running recalculated balance -- nothing posts to a GL
        yet, so there's no ledger to keep in step with.

        quantity_on_hand = receipts + count adjustments - issues - wastage.
        Transfers are excluded: a transfer moves stock between locations but never
        changes the system-wide total, so netting it out of this total is correct
        (per-location balances, if needed later, read straight off the movement
        rows this service already returns via InventoryMovementService).
        """
        if not rows:
            return
        ids = [r.id for r in rows]

        supplier_ids = [r.default_supplier_id for r in rows if r.default_supplier_id]
        suppliers: dict[uuid.UUID, str] = {}
        if supplier_ids:
            suppliers = {c.id: c.name for c in db.scalars(select(Counterparty).where(Counterparty.id.in_(supplier_ids))).all()}

        receipt_rows = db.execute(
            select(InventoryMovement.item_id, InventoryMovement.quantity, InventoryMovement.unit_cost)
            .where(
                InventoryMovement.item_id.in_(ids),
                InventoryMovement.movement_type == "receipt",
                InventoryMovement.is_deleted.is_(False),
            )
        ).all()
        receipt_qty: dict[uuid.UUID, float] = {}
        receipt_value: dict[uuid.UUID, float] = {}
        for item_id, qty, unit_cost in receipt_rows:
            receipt_qty[item_id] = receipt_qty.get(item_id, 0) + float(qty)
            receipt_value[item_id] = receipt_value.get(item_id, 0) + float(qty) * float(unit_cost or 0)

        def _signed_sum(movement_type: str, sign: int) -> dict[uuid.UUID, float]:
            out: dict[uuid.UUID, float] = {}
            for item_id, total in db.execute(
                select(InventoryMovement.item_id, func.sum(InventoryMovement.quantity))
                .where(
                    InventoryMovement.item_id.in_(ids),
                    InventoryMovement.movement_type == movement_type,
                    InventoryMovement.is_deleted.is_(False),
                )
                .group_by(InventoryMovement.item_id)
            ).all():
                out[item_id] = sign * float(total or 0)
            return out

        issues = _signed_sum("issue", -1)
        wastage = _signed_sum("wastage", -1)
        adjustments = _signed_sum("count_adjustment", 1)

        for r in rows:
            r.default_supplier_name = suppliers.get(r.default_supplier_id) if r.default_supplier_id else None
            qty_on_hand = receipt_qty.get(r.id, 0) + issues.get(r.id, 0) + wastage.get(r.id, 0) + adjustments.get(r.id, 0)
            r.quantity_on_hand = qty_on_hand
            r.weighted_average_cost = (receipt_value[r.id] / receipt_qty[r.id]) if receipt_qty.get(r.id) else None
            r.total_value = (qty_on_hand * r.weighted_average_cost) if r.weighted_average_cost is not None else None


class InventoryMovementService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams, item_id: uuid.UUID | None = None) -> tuple[list[InventoryMovement], int]:
        stmt = select(InventoryMovement).where(InventoryMovement.is_deleted.is_(False))
        if item_id is not None:
            stmt = stmt.where(InventoryMovement.item_id == item_id)
        if params.q:
            stmt = stmt.where(InventoryMovement.reference.ilike(f"%{params.q}%"))
        filter_keys = (params.filter_model or {}).keys()
        needs_item_join = params.sort_by in ("item_code", "item_name") or filter_keys & {"item_code", "item_name"}
        needs_supplier_join = params.sort_by == "supplier_name" or "supplier_name" in filter_keys
        if needs_item_join:
            stmt = stmt.join(InventoryItem, InventoryItem.id == InventoryMovement.item_id)
        if needs_supplier_join:
            stmt = stmt.outerjoin(Counterparty, Counterparty.id == InventoryMovement.supplier_id)
        extra_columns = {}
        if needs_item_join:
            extra_columns.update({"item_code": InventoryItem.code, "item_name": InventoryItem.name})
        if needs_supplier_join:
            extra_columns["supplier_name"] = Counterparty.name
        stmt = apply_filters(stmt, InventoryMovement, params.filter_model, extra_columns=extra_columns or None)
        if params.sort_by in ("item_code", "item_name"):
            col = InventoryItem.code if params.sort_by == "item_code" else InventoryItem.name
        elif params.sort_by == "supplier_name":
            col = Counterparty.name
        else:
            col = _sort_col(InventoryMovement, params.sort_by, InventoryMovement.date)
        stmt = stmt.order_by(col.desc() if params.sort_dir != "asc" else col.asc())
        rows, total = paginate(db, stmt, params)
        InventoryMovementService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, movement_id: uuid.UUID) -> InventoryMovement:
        row = db.get(InventoryMovement, movement_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory movement not found.", code="not_found", status_code=404)
        InventoryMovementService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: InventoryMovementCreate) -> InventoryMovement:
        InventoryMovementService._validate(db, payload.item_id, payload.movement_type, payload.location_type,
                                            payload.to_location_type, payload.supplier_id)
        row = InventoryMovement(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="inventory_movement", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        InventoryMovementService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, movement_id: uuid.UUID, payload: InventoryMovementUpdate) -> InventoryMovement:
        row = db.get(InventoryMovement, movement_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory movement not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        InventoryMovementService._validate(
            db,
            data.get("item_id", row.item_id),
            data.get("movement_type", row.movement_type),
            data.get("location_type", row.location_type),
            data.get("to_location_type", row.to_location_type),
            data.get("supplier_id", row.supplier_id),
        )
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="inventory_movement", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        InventoryMovementService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, movement_id: uuid.UUID) -> None:
        row = db.get(InventoryMovement, movement_id)
        if row is None or row.is_deleted:
            raise ApiError("Inventory movement not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="inventory_movement", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate(db: Session, item_id, movement_type, location_type, to_location_type, supplier_id) -> None:
        item = db.get(InventoryItem, item_id)
        if item is None or item.is_deleted:
            raise ApiError("Selected item does not exist.", code="invalid_reference", status_code=400)
        if movement_type not in MOVEMENT_TYPES:
            raise ApiError(f"movement_type must be one of {MOVEMENT_TYPES}.", code="invalid_movement_type", status_code=400)
        if location_type not in LOCATION_TYPES:
            raise ApiError(f"location_type must be one of {LOCATION_TYPES}.", code="invalid_location_type", status_code=400)
        if movement_type == "transfer" and not to_location_type:
            raise ApiError("A transfer needs a destination location.", code="transfer_needs_destination", status_code=400)
        if to_location_type is not None and to_location_type not in LOCATION_TYPES:
            raise ApiError(f"to_location_type must be one of {LOCATION_TYPES}.", code="invalid_location_type", status_code=400)
        if supplier_id is not None:
            supplier = db.get(Counterparty, supplier_id)
            if supplier is None or supplier.is_deleted:
                raise ApiError("Selected supplier does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_relations(db: Session, rows: list[InventoryMovement]) -> None:
        if not rows:
            return
        item_ids = [r.item_id for r in rows]
        items = {i.id: i for i in db.scalars(select(InventoryItem).where(InventoryItem.id.in_(item_ids))).all()}

        supplier_ids = [r.supplier_id for r in rows if r.supplier_id]
        suppliers: dict[uuid.UUID, str] = {}
        if supplier_ids:
            suppliers = {c.id: c.name for c in db.scalars(select(Counterparty).where(Counterparty.id.in_(supplier_ids))).all()}

        for r in rows:
            item = items.get(r.item_id)
            r.item_code = item.code if item else None
            r.item_name = item.name if item else None
            r.supplier_name = suppliers.get(r.supplier_id) if r.supplier_id else None
