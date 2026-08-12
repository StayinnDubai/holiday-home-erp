import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, paginate
from app.models.leasing import EjariRegistration, TenancyContract, TenancyContractParty
from app.models.master_data import Counterparty, Unit
from app.schemas.leasing import (
    EjariRegistrationCreate,
    EjariRegistrationUpdate,
    TenancyContractCreate,
    TenancyContractUpdate,
)
from app.services.audit import AuditService
from app.services.numbering import NumberingService

# doc §1.4: "A unit cannot have two overlapping active inbound contracts." Extended to
# drafts too, so two overlapping drafts for the same unit don't sit unnoticed until
# someone tries to activate both.
OPEN_CONTRACT_STATUSES = ("draft", "active")

# doc §1.4: "A contract term cannot be edited once the contract is active -- renew
# instead." These are the fields that make up the term.
LOCKED_FIELDS_WHEN_ACTIVE = {"unit_id", "start_date", "end_date"}


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


# ---------------------------------------------------------------------------
# Tenancy contracts
# ---------------------------------------------------------------------------
class TenancyContractService:
    @staticmethod
    def list_page(
        db: Session, params: PaginationParams, unit_id: uuid.UUID | None = None
    ) -> tuple[list[TenancyContract], int]:
        stmt = select(TenancyContract).where(TenancyContract.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(TenancyContract.contract_number.ilike(f"%{params.q}%"))
        if unit_id is not None:
            stmt = stmt.where(TenancyContract.unit_id == unit_id)
        if params.sort_by in ("unit_code", "unit_name"):
            stmt = stmt.join(Unit, Unit.id == TenancyContract.unit_id)
            col = Unit.unit_code if params.sort_by == "unit_code" else Unit.unit_name
        else:
            col = _sort_col(TenancyContract, params.sort_by, TenancyContract.contract_number)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        TenancyContractService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, contract_id: uuid.UUID) -> TenancyContract:
        row = db.get(TenancyContract, contract_id)
        if row is None or row.is_deleted:
            raise ApiError("Tenancy contract not found.", code="not_found", status_code=404)
        TenancyContractService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: TenancyContractCreate) -> TenancyContract:
        TenancyContractService._validate_unit(db, payload.unit_id)
        TenancyContractService._validate_landlords(db, payload.landlord_ids)
        TenancyContractService._validate_dates(payload.start_date, payload.end_date)
        TenancyContractService._check_overlap(db, payload.unit_id, payload.start_date, payload.end_date)
        if payload.renewal_of_id is not None:
            TenancyContractService._validate_predecessor(db, payload.renewal_of_id)

        contract_number = NumberingService.next(db, "tenancy_contract")
        data = payload.model_dump(exclude={"landlord_ids"})
        row = TenancyContract(contract_number=contract_number, **data)
        db.add(row)
        db.flush()

        for landlord_id in payload.landlord_ids:
            db.add(TenancyContractParty(contract_id=row.id, landlord_id=landlord_id))

        AuditService.log(db, entity_type="tenancy_contract", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        TenancyContractService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, contract_id: uuid.UUID, payload: TenancyContractUpdate) -> TenancyContract:
        row = db.get(TenancyContract, contract_id)
        if row is None or row.is_deleted:
            raise ApiError("Tenancy contract not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True, exclude={"landlord_ids"})

        if row.status == "active":
            changed_locked = {f for f in LOCKED_FIELDS_WHEN_ACTIVE & data.keys() if data[f] != getattr(row, f)}
            if changed_locked:
                raise ApiError(
                    "This contract is active -- its unit and term dates are immutable. Create a renewal instead.",
                    code="contract_locked",
                    status_code=409,
                )

        new_unit_id = data.get("unit_id", row.unit_id)
        new_start = data.get("start_date", row.start_date)
        new_end = data.get("end_date", row.end_date)
        TenancyContractService._validate_dates(new_start, new_end)
        if "unit_id" in data:
            TenancyContractService._validate_unit(db, new_unit_id)
        if LOCKED_FIELDS_WHEN_ACTIVE & data.keys():
            TenancyContractService._check_overlap(db, new_unit_id, new_start, new_end, exclude_id=row.id)
        if data.get("renewal_of_id") is not None:
            TenancyContractService._validate_predecessor(db, data["renewal_of_id"], exclude_id=row.id)

        for field, value in data.items():
            setattr(row, field, value)

        if payload.landlord_ids is not None:
            TenancyContractService._validate_landlords(db, payload.landlord_ids)
            db.query(TenancyContractParty).filter(TenancyContractParty.contract_id == contract_id).delete()
            for landlord_id in payload.landlord_ids:
                db.add(TenancyContractParty(contract_id=contract_id, landlord_id=landlord_id))

        AuditService.log(db, entity_type="tenancy_contract", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        TenancyContractService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, contract_id: uuid.UUID) -> None:
        row = db.get(TenancyContract, contract_id)
        if row is None or row.is_deleted:
            raise ApiError("Tenancy contract not found.", code="not_found", status_code=404)
        has_ejari = db.scalar(
            select(func.count()).select_from(EjariRegistration)
            .where(EjariRegistration.contract_id == contract_id, EjariRegistration.is_deleted.is_(False))
        )
        if has_ejari:
            raise ApiError("Cannot delete a contract with an Ejari registration attached.", code="in_use", status_code=409)
        has_successor = db.scalar(
            select(func.count()).select_from(TenancyContract)
            .where(TenancyContract.renewal_of_id == contract_id, TenancyContract.is_deleted.is_(False))
        )
        if has_successor:
            raise ApiError("Cannot delete a contract that a renewal links back to.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="tenancy_contract", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unit(db: Session, unit_id: uuid.UUID) -> None:
        unit = db.get(Unit, unit_id)
        if unit is None or unit.is_deleted:
            raise ApiError("Selected unit does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_landlords(db: Session, landlord_ids: list[uuid.UUID]) -> None:
        if not landlord_ids:
            raise ApiError("A tenancy contract needs at least one landlord.", code="landlord_required", status_code=400)
        found = db.scalars(
            select(Counterparty.id).where(Counterparty.id.in_(landlord_ids), Counterparty.is_deleted.is_(False))
        ).all()
        if len(set(found)) != len(set(landlord_ids)):
            raise ApiError("One or more selected landlords do not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_dates(start_date, end_date) -> None:
        if end_date <= start_date:
            raise ApiError("End date must be after start date.", code="invalid_dates", status_code=400)

    @staticmethod
    def _validate_predecessor(db: Session, predecessor_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> None:
        if exclude_id is not None and predecessor_id == exclude_id:
            raise ApiError("A contract cannot be its own renewal.", code="invalid_reference", status_code=400)
        predecessor = db.get(TenancyContract, predecessor_id)
        if predecessor is None or predecessor.is_deleted:
            raise ApiError("Predecessor contract does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _check_overlap(db: Session, unit_id: uuid.UUID, start_date, end_date, exclude_id: uuid.UUID | None = None) -> None:
        stmt = select(TenancyContract.id).where(
            TenancyContract.unit_id == unit_id,
            TenancyContract.is_deleted.is_(False),
            TenancyContract.status.in_(OPEN_CONTRACT_STATUSES),
            TenancyContract.start_date <= end_date,
            TenancyContract.end_date >= start_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(TenancyContract.id != exclude_id)
        if db.scalar(stmt):
            raise ApiError(
                "This unit already has a draft or active tenancy contract covering an overlapping period.",
                code="overlapping_contract",
                status_code=409,
            )

    @staticmethod
    def _attach_relations(db: Session, rows: list[TenancyContract]) -> None:
        if not rows:
            return
        contract_ids = [r.id for r in rows]
        unit_ids = [r.unit_id for r in rows]
        predecessor_ids = [r.renewal_of_id for r in rows if r.renewal_of_id]

        units = {u.id: u for u in db.scalars(select(Unit).where(Unit.id.in_(unit_ids))).all()}

        predecessors: dict[uuid.UUID, TenancyContract] = {}
        if predecessor_ids:
            predecessors = {
                c.id: c for c in db.scalars(select(TenancyContract).where(TenancyContract.id.in_(predecessor_ids))).all()
            }

        successor_rows = db.execute(
            select(TenancyContract.renewal_of_id, TenancyContract.id, TenancyContract.contract_number)
            .where(TenancyContract.renewal_of_id.in_(contract_ids), TenancyContract.is_deleted.is_(False))
        ).all()
        successor_id_by_predecessor = {row[0]: row[1] for row in successor_rows}
        successor_number_by_predecessor = {row[0]: row[2] for row in successor_rows}

        links = db.execute(
            select(TenancyContractParty.contract_id, Counterparty.id, Counterparty.name)
            .join(Counterparty, Counterparty.id == TenancyContractParty.landlord_id)
            .where(TenancyContractParty.contract_id.in_(contract_ids))
        ).all()
        ids_by_contract: dict[uuid.UUID, list[uuid.UUID]] = {}
        names_by_contract: dict[uuid.UUID, list[str]] = {}
        for contract_id, landlord_id, landlord_name in links:
            ids_by_contract.setdefault(contract_id, []).append(landlord_id)
            names_by_contract.setdefault(contract_id, []).append(landlord_name)

        for r in rows:
            unit = units.get(r.unit_id)
            r.unit_code = unit.unit_code if unit else None
            r.unit_name = unit.unit_name if unit else None
            r.landlord_ids = ids_by_contract.get(r.id, [])
            r.landlord_names = ", ".join(names_by_contract.get(r.id, []))

            r.renewal_of_contract_number = None
            r.gap_days = None
            if r.renewal_of_id:
                predecessor = predecessors.get(r.renewal_of_id)
                if predecessor:
                    r.renewal_of_contract_number = predecessor.contract_number
                    gap = (r.start_date - predecessor.end_date).days - 1
                    r.gap_days = gap if gap > 0 else None

            r.renewed_by_id = successor_id_by_predecessor.get(r.id)
            r.renewed_by_contract_number = successor_number_by_predecessor.get(r.id)


# ---------------------------------------------------------------------------
# Ejari registrations
# ---------------------------------------------------------------------------
class EjariRegistrationService:
    @staticmethod
    def list_page(
        db: Session, params: PaginationParams, unit_id: uuid.UUID | None = None
    ) -> tuple[list[EjariRegistration], int]:
        stmt = select(EjariRegistration).where(EjariRegistration.is_deleted.is_(False))
        contract_joined = False
        if params.q:
            stmt = stmt.where(EjariRegistration.ejari_contract_number.ilike(f"%{params.q}%"))
        if unit_id is not None:
            # Ejari relates to a unit indirectly, via its contract (doc §1.4: one
            # contract per unit) -- join rather than a denormalized unit_id column.
            stmt = stmt.join(TenancyContract, TenancyContract.id == EjariRegistration.contract_id).where(
                TenancyContract.unit_id == unit_id
            )
            contract_joined = True
        if params.sort_by == "contract_number":
            if not contract_joined:
                stmt = stmt.join(TenancyContract, TenancyContract.id == EjariRegistration.contract_id)
            col = TenancyContract.contract_number
        else:
            col = _sort_col(EjariRegistration, params.sort_by, EjariRegistration.registration_date)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        EjariRegistrationService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, ejari_id: uuid.UUID) -> EjariRegistration:
        row = db.get(EjariRegistration, ejari_id)
        if row is None or row.is_deleted:
            raise ApiError("Ejari registration not found.", code="not_found", status_code=404)
        EjariRegistrationService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: EjariRegistrationCreate) -> EjariRegistration:
        EjariRegistrationService._validate_contract(db, payload.contract_id)
        EjariRegistrationService._check_one_per_contract(db, payload.contract_id)

        row = EjariRegistration(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="ejari_registration", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        EjariRegistrationService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, ejari_id: uuid.UUID, payload: EjariRegistrationUpdate) -> EjariRegistration:
        row = db.get(EjariRegistration, ejari_id)
        if row is None or row.is_deleted:
            raise ApiError("Ejari registration not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "contract_id" in data and data["contract_id"] != row.contract_id:
            EjariRegistrationService._validate_contract(db, data["contract_id"])
            EjariRegistrationService._check_one_per_contract(db, data["contract_id"], exclude_id=ejari_id)

        for field, value in data.items():
            setattr(row, field, value)

        AuditService.log(db, entity_type="ejari_registration", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        EjariRegistrationService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, ejari_id: uuid.UUID) -> None:
        row = db.get(EjariRegistration, ejari_id)
        if row is None or row.is_deleted:
            raise ApiError("Ejari registration not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="ejari_registration", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_contract(db: Session, contract_id: uuid.UUID) -> None:
        contract = db.get(TenancyContract, contract_id)
        if contract is None or contract.is_deleted:
            raise ApiError("Selected contract does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _check_one_per_contract(db: Session, contract_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> None:
        # doc §1.4 Q183: "one property per Ejari" -- one registration per contract.
        stmt = select(func.count()).select_from(EjariRegistration).where(
            EjariRegistration.contract_id == contract_id, EjariRegistration.is_deleted.is_(False)
        )
        if exclude_id is not None:
            stmt = stmt.where(EjariRegistration.id != exclude_id)
        if db.scalar(stmt):
            raise ApiError(
                "This contract already has an Ejari registration -- one per contract.",
                code="ejari_exists",
                status_code=409,
            )

    @staticmethod
    def _attach_relations(db: Session, rows: list[EjariRegistration]) -> None:
        if not rows:
            return
        contract_ids = [r.contract_id for r in rows]
        contracts = {c.id: c for c in db.scalars(select(TenancyContract).where(TenancyContract.id.in_(contract_ids))).all()}
        for r in rows:
            contract = contracts.get(r.contract_id)
            r.contract_number = contract.contract_number if contract else None
            r.variance_warnings = EjariRegistrationService._variance_warnings(r, contract)

    @staticmethod
    def _variance_warnings(row: EjariRegistration, contract: TenancyContract | None) -> list[str]:
        # doc §1.4 "Ejari-versus-contract variance check": compares start date, end
        # date, actual annual amount vs. rent, and security deposit. Warned, never
        # blocked -- legitimate divergence exists.
        warnings: list[str] = []
        if contract is None:
            return warnings
        if row.start_date and row.start_date != contract.start_date:
            warnings.append("Start date differs from the contract")
        if row.end_date and row.end_date != contract.end_date:
            warnings.append("End date differs from the contract")

        actual_annual = row.actual_annual_amount if row.actual_annual_amount is not None else row.annual_amount
        if actual_annual is not None and contract.total_annual_rent is not None:
            if round(actual_annual, 2) != round(contract.total_annual_rent, 2):
                warnings.append("Actual annual amount differs from the contract's annual rent")

        if row.security_deposit is not None and contract.security_deposit_amount is not None:
            if round(row.security_deposit, 2) != round(contract.security_deposit_amount, 2):
                warnings.append("Security deposit differs from the contract")

        return warnings
