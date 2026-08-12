import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.foundation import Currency
from app.schemas.foundation import CurrencyCreate, CurrencyUpdate
from app.services.audit import AuditService


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


class CurrencyService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Currency], int]:
        stmt = select(Currency).where(Currency.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Currency.name.ilike(f"%{params.q}%") | Currency.full_name.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, Currency, params.filter_model)
        col = _sort_col(Currency, params.sort_by, Currency.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, currency_id: uuid.UUID) -> Currency:
        row = db.get(Currency, currency_id)
        if row is None or row.is_deleted:
            raise ApiError("Currency not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: CurrencyCreate) -> Currency:
        CurrencyService._validate_unique_code(db, payload.code)
        row = Currency(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="currency", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, currency_id: uuid.UUID, payload: CurrencyUpdate) -> Currency:
        row = db.get(Currency, currency_id)
        if row is None or row.is_deleted:
            raise ApiError("Currency not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            CurrencyService._validate_unique_code(db, data["code"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="currency", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, currency_id: uuid.UUID) -> None:
        row = db.get(Currency, currency_id)
        if row is None or row.is_deleted:
            raise ApiError("Currency not found.", code="not_found", status_code=404)
        CurrencyService._check_not_in_use(db, currency_id)
        row.is_deleted = True
        AuditService.log(db, entity_type="currency", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(Currency.id).where(Currency.code == code, Currency.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Currency code '{code}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _check_not_in_use(db: Session, currency_id: uuid.UUID) -> None:
        # Imported lazily to avoid a foundation <-> accounting import cycle.
        from app.models.accounting import BankAccount
        from app.models.foundation import Entity

        in_use = db.scalar(
            select(func.count()).select_from(Entity).where(Entity.base_currency_id == currency_id)
        ) or db.scalar(
            select(func.count()).select_from(BankAccount).where(
                BankAccount.currency_id == currency_id, BankAccount.is_deleted.is_(False)
            )
        )
        if in_use:
            raise ApiError("Cannot delete a currency that is still referenced elsewhere.", code="in_use", status_code=409)
