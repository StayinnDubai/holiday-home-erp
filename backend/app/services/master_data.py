import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.master_data import (
    Building,
    BuildingAmenity,
    BuildingContact,
    BuildingDeposit,
    Counterparty,
    CounterpartyGroup,
    Unit,
    UnitLandlord,
    UnitSpace,
)
from app.schemas.master_data import (
    BuildingAmenityCreate,
    BuildingAmenityUpdate,
    BuildingContactCreate,
    BuildingContactUpdate,
    BuildingCreate,
    BuildingDepositCreate,
    BuildingDepositUpdate,
    BuildingUpdate,
    CounterpartyCreate,
    CounterpartyGroupCreate,
    CounterpartyGroupUpdate,
    CounterpartyUpdate,
    UnitCreate,
    UnitSpaceCreate,
    UnitSpaceUpdate,
    UnitUpdate,
)
from app.services.audit import AuditService
from app.services.numbering import NumberingService


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------
class BuildingService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Building], int]:
        stmt = select(Building).where(Building.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Building.name.ilike(f"%{params.q}%"))
        unit_count_col = (
            select(func.count(Unit.id))
            .where(Unit.building_id == Building.id, Unit.is_deleted.is_(False))
            .correlate(Building)
            .scalar_subquery()
        )
        stmt = apply_filters(stmt, Building, params.filter_model, extra_columns={"unit_count": unit_count_col})
        order_col = unit_count_col if params.sort_by == "unit_count" else _sort_col(Building, params.sort_by, Building.name)
        stmt = stmt.order_by(order_col.asc() if params.sort_dir != "desc" else order_col.desc())
        rows, total = paginate(db, stmt, params)
        BuildingService._attach_unit_counts(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, building_id: uuid.UUID) -> Building:
        row = db.get(Building, building_id)
        if row is None or row.is_deleted:
            raise ApiError("Building not found.", code="not_found", status_code=404)
        BuildingService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BuildingCreate) -> Building:
        row = Building(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="building", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        BuildingService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def update(db: Session, building_id: uuid.UUID, payload: BuildingUpdate) -> Building:
        row = db.get(Building, building_id)
        if row is None or row.is_deleted:
            raise ApiError("Building not found.", code="not_found", status_code=404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="building", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        BuildingService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, building_id: uuid.UUID) -> None:
        row = db.get(Building, building_id)
        if row is None or row.is_deleted:
            raise ApiError("Building not found.", code="not_found", status_code=404)
        in_use = db.scalar(select(func.count()).select_from(Unit).where(Unit.building_id == building_id, Unit.is_deleted.is_(False)))
        if in_use:
            raise ApiError("Cannot delete a building that still has units.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="building", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _attach_unit_counts(db: Session, rows: list[Building]) -> None:
        if not rows:
            return
        ids = [r.id for r in rows]
        counts = dict(
            db.execute(
                select(Unit.building_id, func.count())
                .where(Unit.building_id.in_(ids), Unit.is_deleted.is_(False))
                .group_by(Unit.building_id)
            ).all()
        )
        for r in rows:
            r.unit_count = counts.get(r.id, 0)


# ---------------------------------------------------------------------------
# Building contacts, amenities, deposits and fees (doc §1.3)
# ---------------------------------------------------------------------------
def _validate_building_exists(db: Session, building_id: uuid.UUID) -> None:
    building = db.get(Building, building_id)
    if building is None or building.is_deleted:
        raise ApiError("Selected building does not exist.", code="invalid_reference", status_code=400)


def _attach_building_names(db: Session, rows: list, building_id_attr: str = "building_id") -> None:
    if not rows:
        return
    ids = [getattr(r, building_id_attr) for r in rows]
    names = {b.id: b.name for b in db.scalars(select(Building).where(Building.id.in_(ids))).all()}
    for r in rows:
        r.building_name = names.get(getattr(r, building_id_attr))


def _sort_col_with_building_name(stmt: Select, model, params: PaginationParams, default):
    """`building_name` is a display column joined in at read time (`_attach_building_names`),
    not a real column on `model` -- `_sort_col`'s `hasattr` check misses it, so a click on
    that header silently no-ops. Join it in for real only when it's actually the sort key
    or being filtered on (`apply_filters`' `extra_columns`)."""
    needs_join = params.sort_by == "building_name" or (params.filter_model or {}).get("building_name")
    if needs_join:
        stmt = stmt.outerjoin(Building, Building.id == model.building_id)
    stmt = apply_filters(stmt, model, params.filter_model, extra_columns={"building_name": Building.name} if needs_join else None)
    order_col = Building.name if params.sort_by == "building_name" else _sort_col(model, params.sort_by, default)
    return stmt, order_col


class BuildingContactService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BuildingContact], int]:
        stmt = select(BuildingContact).where(BuildingContact.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(BuildingContact.name.ilike(f"%{params.q}%"))
        stmt, col = _sort_col_with_building_name(stmt, BuildingContact, params, BuildingContact.name)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        _attach_building_names(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, contact_id: uuid.UUID) -> BuildingContact:
        row = db.get(BuildingContact, contact_id)
        if row is None or row.is_deleted:
            raise ApiError("Building contact not found.", code="not_found", status_code=404)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BuildingContactCreate) -> BuildingContact:
        _validate_building_exists(db, payload.building_id)
        row = BuildingContact(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="building_contact", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def update(db: Session, contact_id: uuid.UUID, payload: BuildingContactUpdate) -> BuildingContact:
        row = db.get(BuildingContact, contact_id)
        if row is None or row.is_deleted:
            raise ApiError("Building contact not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "building_id" in data:
            _validate_building_exists(db, data["building_id"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="building_contact", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, contact_id: uuid.UUID) -> None:
        row = db.get(BuildingContact, contact_id)
        if row is None or row.is_deleted:
            raise ApiError("Building contact not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="building_contact", entity_id=row.id, action="delete")
        db.commit()


class BuildingAmenityService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BuildingAmenity], int]:
        stmt = select(BuildingAmenity).where(BuildingAmenity.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(BuildingAmenity.name.ilike(f"%{params.q}%"))
        stmt, col = _sort_col_with_building_name(stmt, BuildingAmenity, params, BuildingAmenity.name)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        _attach_building_names(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, amenity_id: uuid.UUID) -> BuildingAmenity:
        row = db.get(BuildingAmenity, amenity_id)
        if row is None or row.is_deleted:
            raise ApiError("Building amenity not found.", code="not_found", status_code=404)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BuildingAmenityCreate) -> BuildingAmenity:
        _validate_building_exists(db, payload.building_id)
        row = BuildingAmenity(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="building_amenity", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def update(db: Session, amenity_id: uuid.UUID, payload: BuildingAmenityUpdate) -> BuildingAmenity:
        row = db.get(BuildingAmenity, amenity_id)
        if row is None or row.is_deleted:
            raise ApiError("Building amenity not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "building_id" in data:
            _validate_building_exists(db, data["building_id"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="building_amenity", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, amenity_id: uuid.UUID) -> None:
        row = db.get(BuildingAmenity, amenity_id)
        if row is None or row.is_deleted:
            raise ApiError("Building amenity not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="building_amenity", entity_id=row.id, action="delete")
        db.commit()


class BuildingDepositService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BuildingDeposit], int]:
        stmt = select(BuildingDeposit).where(BuildingDeposit.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(BuildingDeposit.description.ilike(f"%{params.q}%"))
        stmt, col = _sort_col_with_building_name(stmt, BuildingDeposit, params, BuildingDeposit.date)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        _attach_building_names(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, deposit_id: uuid.UUID) -> BuildingDeposit:
        row = db.get(BuildingDeposit, deposit_id)
        if row is None or row.is_deleted:
            raise ApiError("Building deposit not found.", code="not_found", status_code=404)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BuildingDepositCreate) -> BuildingDeposit:
        _validate_building_exists(db, payload.building_id)
        row = BuildingDeposit(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="building_deposit", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def update(db: Session, deposit_id: uuid.UUID, payload: BuildingDepositUpdate) -> BuildingDeposit:
        row = db.get(BuildingDeposit, deposit_id)
        if row is None or row.is_deleted:
            raise ApiError("Building deposit not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "building_id" in data:
            _validate_building_exists(db, data["building_id"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="building_deposit", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        _attach_building_names(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, deposit_id: uuid.UUID) -> None:
        row = db.get(BuildingDeposit, deposit_id)
        if row is None or row.is_deleted:
            raise ApiError("Building deposit not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="building_deposit", entity_id=row.id, action="delete")
        db.commit()


# ---------------------------------------------------------------------------
# Counterparties
# ---------------------------------------------------------------------------
class CounterpartyService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams, landlord_only: bool = False) -> tuple[list[Counterparty], int]:
        stmt = select(Counterparty).where(Counterparty.is_deleted.is_(False))
        group_joined = False
        if landlord_only:
            stmt = stmt.join(CounterpartyGroup, CounterpartyGroup.id == Counterparty.group_id).where(
                CounterpartyGroup.is_landlord_group.is_(True)
            )
            group_joined = True
        if params.q:
            stmt = stmt.where(Counterparty.name.ilike(f"%{params.q}%"))

        unit_count_col = (
            select(func.count(UnitLandlord.id))
            .join(Unit, Unit.id == UnitLandlord.unit_id)
            .where(UnitLandlord.landlord_id == Counterparty.id, Unit.is_deleted.is_(False))
            .correlate(Counterparty)
            .scalar_subquery()
        )
        needs_group_filter_join = not group_joined and (params.filter_model or {}).get("group_name")
        if needs_group_filter_join:
            stmt = stmt.outerjoin(CounterpartyGroup, CounterpartyGroup.id == Counterparty.group_id)
        stmt = apply_filters(
            stmt, Counterparty, params.filter_model, extra_columns={"unit_count": unit_count_col, "group_name": CounterpartyGroup.name}
        )

        if params.sort_by == "unit_count":
            order_col = unit_count_col
        elif params.sort_by == "group_name":
            if not group_joined and not needs_group_filter_join:
                stmt = stmt.outerjoin(CounterpartyGroup, CounterpartyGroup.id == Counterparty.group_id)
            order_col = CounterpartyGroup.name
        else:
            order_col = _sort_col(Counterparty, params.sort_by, Counterparty.name)
        stmt = stmt.order_by(order_col.asc() if params.sort_dir != "desc" else order_col.desc())
        rows, total = paginate(db, stmt, params)
        CounterpartyService._attach_unit_counts(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, counterparty_id: uuid.UUID) -> Counterparty:
        row = db.get(Counterparty, counterparty_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty not found.", code="not_found", status_code=404)
        CounterpartyService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: CounterpartyCreate) -> Counterparty:
        if payload.group_id is not None:
            CounterpartyService._validate_group(db, payload.group_id)
        row = Counterparty(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="counterparty", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        CounterpartyService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def update(db: Session, counterparty_id: uuid.UUID, payload: CounterpartyUpdate) -> Counterparty:
        row = db.get(Counterparty, counterparty_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if data.get("group_id") is not None:
            CounterpartyService._validate_group(db, data["group_id"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="counterparty", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        CounterpartyService._attach_unit_counts(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, counterparty_id: uuid.UUID) -> None:
        row = db.get(Counterparty, counterparty_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty not found.", code="not_found", status_code=404)
        in_use = db.scalar(
            select(func.count()).select_from(UnitLandlord).join(Unit, Unit.id == UnitLandlord.unit_id)
            .where(UnitLandlord.landlord_id == counterparty_id, Unit.is_deleted.is_(False))
        )
        if in_use:
            raise ApiError("Cannot delete a landlord that still co-owns units.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="counterparty", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_group(db: Session, group_id: uuid.UUID) -> None:
        group = db.get(CounterpartyGroup, group_id)
        if group is None or group.is_deleted:
            raise ApiError("Selected counterparty group does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_unit_counts(db: Session, rows: list[Counterparty]) -> None:
        if not rows:
            return
        ids = [r.id for r in rows]
        counts = dict(
            db.execute(
                select(UnitLandlord.landlord_id, func.count())
                .join(Unit, Unit.id == UnitLandlord.unit_id)
                .where(UnitLandlord.landlord_id.in_(ids), Unit.is_deleted.is_(False))
                .group_by(UnitLandlord.landlord_id)
            ).all()
        )
        group_ids = [r.group_id for r in rows if r.group_id]
        group_names: dict[uuid.UUID, str] = {}
        if group_ids:
            group_names = {g.id: g.name for g in db.scalars(select(CounterpartyGroup).where(CounterpartyGroup.id.in_(group_ids))).all()}
        for r in rows:
            r.unit_count = counts.get(r.id, 0)
            r.group_name = group_names.get(r.group_id) if r.group_id else None


# ---------------------------------------------------------------------------
# Counterparty groups (Accounting > Counterparty Group)
# ---------------------------------------------------------------------------
class CounterpartyGroupService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[CounterpartyGroup], int]:
        stmt = select(CounterpartyGroup).where(CounterpartyGroup.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(CounterpartyGroup.name.ilike(f"%{params.q}%") | CounterpartyGroup.code.ilike(f"%{params.q}%"))
        counterparty_count_col = (
            select(func.count(Counterparty.id))
            .where(Counterparty.group_id == CounterpartyGroup.id, Counterparty.is_deleted.is_(False))
            .correlate(CounterpartyGroup)
            .scalar_subquery()
        )
        stmt = apply_filters(
            stmt, CounterpartyGroup, params.filter_model, extra_columns={"counterparty_count": counterparty_count_col}
        )
        order_col = (
            counterparty_count_col
            if params.sort_by == "counterparty_count"
            else _sort_col(CounterpartyGroup, params.sort_by, CounterpartyGroup.code)
        )
        stmt = stmt.order_by(order_col.asc() if params.sort_dir != "desc" else order_col.desc())
        rows, total = paginate(db, stmt, params)
        CounterpartyGroupService._attach_counterparty_counts(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, group_id: uuid.UUID) -> CounterpartyGroup:
        row = db.get(CounterpartyGroup, group_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty group not found.", code="not_found", status_code=404)
        CounterpartyGroupService._attach_counterparty_counts(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: CounterpartyGroupCreate) -> CounterpartyGroup:
        CounterpartyGroupService._validate_unique_code(db, payload.code)
        row = CounterpartyGroup(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="counterparty_group", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        CounterpartyGroupService._attach_counterparty_counts(db, [row])
        return row

    @staticmethod
    def update(db: Session, group_id: uuid.UUID, payload: CounterpartyGroupUpdate) -> CounterpartyGroup:
        row = db.get(CounterpartyGroup, group_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty group not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            CounterpartyGroupService._validate_unique_code(db, data["code"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="counterparty_group", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        CounterpartyGroupService._attach_counterparty_counts(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, group_id: uuid.UUID) -> None:
        row = db.get(CounterpartyGroup, group_id)
        if row is None or row.is_deleted:
            raise ApiError("Counterparty group not found.", code="not_found", status_code=404)
        in_use = db.scalar(
            select(func.count()).select_from(Counterparty).where(Counterparty.group_id == group_id, Counterparty.is_deleted.is_(False))
        )
        if in_use:
            raise ApiError("Cannot delete a group that still has counterparties assigned to it.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="counterparty_group", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(CounterpartyGroup.id).where(CounterpartyGroup.code == code, CounterpartyGroup.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Counterparty group code '{code}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _attach_counterparty_counts(db: Session, rows: list[CounterpartyGroup]) -> None:
        if not rows:
            return
        ids = [r.id for r in rows]
        counts = dict(
            db.execute(
                select(Counterparty.group_id, func.count())
                .where(Counterparty.group_id.in_(ids), Counterparty.is_deleted.is_(False))
                .group_by(Counterparty.group_id)
            ).all()
        )
        for r in rows:
            r.counterparty_count = counts.get(r.id, 0)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
class UnitService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Unit], int]:
        stmt = select(Unit).where(Unit.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Unit.unit_name.ilike(f"%{params.q}%") | Unit.unit_code.ilike(f"%{params.q}%"))
        stmt, order_col = _sort_col_with_building_name(stmt, Unit, params, Unit.unit_code)
        stmt = stmt.order_by(order_col.asc() if params.sort_dir != "desc" else order_col.desc())
        rows, total = paginate(db, stmt, params)
        UnitService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, unit_id: uuid.UUID) -> Unit:
        row = db.get(Unit, unit_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit not found.", code="not_found", status_code=404)
        UnitService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: UnitCreate) -> Unit:
        UnitService._validate_building(db, payload.building_id)
        UnitService._validate_landlords(db, payload.landlord_ids)

        unit_code = UnitService._next_unit_code(db)
        data = payload.model_dump(exclude={"landlord_ids"})
        row = Unit(unit_code=unit_code, **data)
        db.add(row)
        db.flush()

        for landlord_id in payload.landlord_ids:
            db.add(UnitLandlord(unit_id=row.id, landlord_id=landlord_id))

        AuditService.log(db, entity_type="unit", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        UnitService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, unit_id: uuid.UUID, payload: UnitUpdate) -> Unit:
        row = db.get(Unit, unit_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True, exclude={"landlord_ids"})
        if "building_id" in data:
            UnitService._validate_building(db, data["building_id"])
        for field, value in data.items():
            setattr(row, field, value)

        if payload.landlord_ids is not None:
            UnitService._validate_landlords(db, payload.landlord_ids)
            db.query(UnitLandlord).filter(UnitLandlord.unit_id == unit_id).delete()
            for landlord_id in payload.landlord_ids:
                db.add(UnitLandlord(unit_id=unit_id, landlord_id=landlord_id))

        AuditService.log(db, entity_type="unit", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        UnitService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, unit_id: uuid.UUID) -> None:
        row = db.get(Unit, unit_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="unit", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_building(db: Session, building_id: uuid.UUID) -> None:
        building = db.get(Building, building_id)
        if building is None or building.is_deleted:
            raise ApiError("Selected building does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_landlords(db: Session, landlord_ids: list[uuid.UUID]) -> None:
        if not landlord_ids:
            raise ApiError("A unit needs at least one landlord.", code="landlord_required", status_code=400)
        found = db.scalars(
            select(Counterparty.id).where(Counterparty.id.in_(landlord_ids), Counterparty.is_deleted.is_(False))
        ).all()
        if len(set(found)) != len(set(landlord_ids)):
            raise ApiError("One or more selected landlords do not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _next_unit_code(db: Session) -> str:
        # doc §1.1: sequential, zero-padded to three digits, never reused.
        number = NumberingService.raw_next(db, "unit_code")
        return f"{number:03d}"

    @staticmethod
    def _attach_relations(db: Session, rows: list[Unit]) -> None:
        if not rows:
            return
        unit_ids = [r.id for r in rows]
        building_ids = [r.building_id for r in rows]

        buildings = {b.id: b.name for b in db.scalars(select(Building).where(Building.id.in_(building_ids))).all()}

        links = db.execute(
            select(UnitLandlord.unit_id, Counterparty.id, Counterparty.name)
            .join(Counterparty, Counterparty.id == UnitLandlord.landlord_id)
            .where(UnitLandlord.unit_id.in_(unit_ids))
        ).all()
        ids_by_unit: dict[uuid.UUID, list[uuid.UUID]] = {}
        names_by_unit: dict[uuid.UUID, list[str]] = {}
        for unit_id, landlord_id, landlord_name in links:
            ids_by_unit.setdefault(unit_id, []).append(landlord_id)
            names_by_unit.setdefault(unit_id, []).append(landlord_name)

        for r in rows:
            r.building_name = buildings.get(r.building_id)
            r.landlord_ids = ids_by_unit.get(r.id, [])
            r.landlord_names = ", ".join(names_by_unit.get(r.id, []))


# ---------------------------------------------------------------------------
# Unit spaces (layout components, doc §1.1 `UnitSpace`)
# ---------------------------------------------------------------------------
class UnitSpaceService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams, unit_id: uuid.UUID | None = None) -> tuple[list[UnitSpace], int]:
        stmt = select(UnitSpace).where(UnitSpace.is_deleted.is_(False))
        if unit_id is not None:
            stmt = stmt.where(UnitSpace.unit_id == unit_id)
        if params.q:
            stmt = stmt.where(UnitSpace.name.ilike(f"%{params.q}%"))
        col = _sort_col(UnitSpace, params.sort_by, UnitSpace.space_type)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, space_id: uuid.UUID) -> UnitSpace:
        row = db.get(UnitSpace, space_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit space not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: UnitSpaceCreate) -> UnitSpace:
        unit = db.get(Unit, payload.unit_id)
        if unit is None or unit.is_deleted:
            raise ApiError("Selected unit does not exist.", code="invalid_reference", status_code=400)
        row = UnitSpace(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="unit_space", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, space_id: uuid.UUID, payload: UnitSpaceUpdate) -> UnitSpace:
        row = db.get(UnitSpace, space_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit space not found.", code="not_found", status_code=404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="unit_space", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, space_id: uuid.UUID) -> None:
        row = db.get(UnitSpace, space_id)
        if row is None or row.is_deleted:
            raise ApiError("Unit space not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="unit_space", entity_id=row.id, action="delete")
        db.commit()
