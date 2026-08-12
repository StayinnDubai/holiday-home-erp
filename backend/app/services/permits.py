import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.leasing import TenancyContract
from app.models.master_data import Unit
from app.models.permits import DtcmPermit
from app.schemas.permits import DtcmPermitCreate, DtcmPermitUpdate
from app.services.audit import AuditService


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


class DtcmPermitService:
    @staticmethod
    def list_page(
        db: Session, params: PaginationParams, unit_id: uuid.UUID | None = None
    ) -> tuple[list[DtcmPermit], int]:
        stmt = select(DtcmPermit).where(DtcmPermit.is_deleted.is_(False))
        if unit_id is not None:
            stmt = stmt.where(DtcmPermit.unit_id == unit_id)
        if params.q:
            stmt = stmt.where(DtcmPermit.permit_number.ilike(f"%{params.q}%"))
        needs_unit_join = params.sort_by == "unit_code" or "unit_code" in (params.filter_model or {})
        if needs_unit_join:
            stmt = stmt.join(Unit, Unit.id == DtcmPermit.unit_id)
        stmt = apply_filters(
            stmt, DtcmPermit, params.filter_model, extra_columns={"unit_code": Unit.unit_code} if needs_unit_join else None
        )
        if params.sort_by == "unit_code":
            col = Unit.unit_code
        else:
            col = _sort_col(DtcmPermit, params.sort_by, DtcmPermit.permit_number)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        DtcmPermitService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, permit_id: uuid.UUID) -> DtcmPermit:
        row = db.get(DtcmPermit, permit_id)
        if row is None or row.is_deleted:
            raise ApiError("DTCM permit not found.", code="not_found", status_code=404)
        DtcmPermitService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: DtcmPermitCreate) -> DtcmPermit:
        DtcmPermitService._validate_unit(db, payload.unit_id)
        if payload.contract_id is not None:
            DtcmPermitService._validate_contract(db, payload.contract_id)
        DtcmPermitService._validate_unique_permit_number(db, payload.permit_number)

        row = DtcmPermit(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="dtcm_permit", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        DtcmPermitService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, permit_id: uuid.UUID, payload: DtcmPermitUpdate) -> DtcmPermit:
        row = db.get(DtcmPermit, permit_id)
        if row is None or row.is_deleted:
            raise ApiError("DTCM permit not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "unit_id" in data:
            DtcmPermitService._validate_unit(db, data["unit_id"])
        if data.get("contract_id") is not None:
            DtcmPermitService._validate_contract(db, data["contract_id"])
        if "permit_number" in data and data["permit_number"] != row.permit_number:
            DtcmPermitService._validate_unique_permit_number(db, data["permit_number"])

        for field, value in data.items():
            setattr(row, field, value)

        AuditService.log(db, entity_type="dtcm_permit", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        DtcmPermitService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, permit_id: uuid.UUID) -> None:
        row = db.get(DtcmPermit, permit_id)
        if row is None or row.is_deleted:
            raise ApiError("DTCM permit not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="dtcm_permit", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unit(db: Session, unit_id: uuid.UUID) -> None:
        unit = db.get(Unit, unit_id)
        if unit is None or unit.is_deleted:
            raise ApiError("Selected unit does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_contract(db: Session, contract_id: uuid.UUID) -> None:
        contract = db.get(TenancyContract, contract_id)
        if contract is None or contract.is_deleted:
            raise ApiError("Selected contract does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_unique_permit_number(db: Session, permit_number: str) -> None:
        existing = db.scalar(
            select(DtcmPermit.id).where(DtcmPermit.permit_number == permit_number, DtcmPermit.is_deleted.is_(False))
        )
        if existing:
            raise ApiError(f"Permit number '{permit_number}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _attach_relations(db: Session, rows: list[DtcmPermit]) -> None:
        if not rows:
            return
        unit_ids = [r.unit_id for r in rows]
        units = {u.id: u.unit_code for u in db.scalars(select(Unit).where(Unit.id.in_(unit_ids))).all()}

        contract_ids = [r.contract_id for r in rows if r.contract_id]
        contracts: dict[uuid.UUID, str] = {}
        if contract_ids:
            contracts = {
                c.id: c.contract_number for c in db.scalars(select(TenancyContract).where(TenancyContract.id.in_(contract_ids))).all()
            }

        for r in rows:
            r.unit_code = units.get(r.unit_id)
            r.contract_number = contracts.get(r.contract_id) if r.contract_id else None
