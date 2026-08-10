import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, paginate
from app.models.master_data import Building, Counterparty, Unit, UnitLandlord
from app.schemas.master_data import BuildingCreate, BuildingUpdate, CounterpartyCreate, CounterpartyUpdate, UnitCreate, UnitUpdate
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
        stmt = stmt.order_by(_sort_col(Building, params.sort_by, Building.name).asc() if params.sort_dir != "desc"
                              else _sort_col(Building, params.sort_by, Building.name).desc())
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
# Counterparties
# ---------------------------------------------------------------------------
class CounterpartyService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Counterparty], int]:
        stmt = select(Counterparty).where(Counterparty.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Counterparty.name.ilike(f"%{params.q}%"))
        stmt = stmt.order_by(_sort_col(Counterparty, params.sort_by, Counterparty.name).asc() if params.sort_dir != "desc"
                              else _sort_col(Counterparty, params.sort_by, Counterparty.name).desc())
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
        for field, value in payload.model_dump(exclude_unset=True).items():
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
        for r in rows:
            r.unit_count = counts.get(r.id, 0)


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
class UnitService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Unit], int]:
        stmt = select(Unit).where(Unit.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Unit.unit_name.ilike(f"%{params.q}%") | Unit.unit_code.ilike(f"%{params.q}%"))
        stmt = stmt.order_by(_sort_col(Unit, params.sort_by, Unit.unit_code).asc() if params.sort_dir != "desc"
                              else _sort_col(Unit, params.sort_by, Unit.unit_code).desc())
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
