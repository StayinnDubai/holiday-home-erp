import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.foundation import AssetCategory, CostType, Currency, TaxCode
from app.schemas.foundation import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    CostTypeCreate,
    CostTypeUpdate,
    CurrencyCreate,
    CurrencyUpdate,
    TaxCodeCreate,
    TaxCodeUpdate,
)
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


class TaxCodeService:
    """Settings > Tax Codes (doc §5.7) -- mirrors CurrencyService's shape."""

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[TaxCode], int]:
        stmt = select(TaxCode).where(TaxCode.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(TaxCode.code.ilike(f"%{params.q}%") | TaxCode.name.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, TaxCode, params.filter_model)
        col = _sort_col(TaxCode, params.sort_by, TaxCode.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, tax_code_id: uuid.UUID) -> TaxCode:
        row = db.get(TaxCode, tax_code_id)
        if row is None or row.is_deleted:
            raise ApiError("Tax code not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: TaxCodeCreate) -> TaxCode:
        TaxCodeService._validate_unique_code(db, payload.code)
        row = TaxCode(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="tax_code", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, tax_code_id: uuid.UUID, payload: TaxCodeUpdate) -> TaxCode:
        row = db.get(TaxCode, tax_code_id)
        if row is None or row.is_deleted:
            raise ApiError("Tax code not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            TaxCodeService._validate_unique_code(db, data["code"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="tax_code", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, tax_code_id: uuid.UUID) -> None:
        row = db.get(TaxCode, tax_code_id)
        if row is None or row.is_deleted:
            raise ApiError("Tax code not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="tax_code", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(TaxCode.id).where(TaxCode.code == code, TaxCode.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Tax code '{code}' is already in use.", code="duplicate_code", status_code=409)


class AssetCategoryService:
    """Settings > Asset Categories -- pure reference data, mirrors CurrencyService."""

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[AssetCategory], int]:
        stmt = select(AssetCategory).where(AssetCategory.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(AssetCategory.code.ilike(f"%{params.q}%") | AssetCategory.name.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, AssetCategory, params.filter_model)
        col = _sort_col(AssetCategory, params.sort_by, AssetCategory.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, category_id: uuid.UUID) -> AssetCategory:
        row = db.get(AssetCategory, category_id)
        if row is None or row.is_deleted:
            raise ApiError("Asset category not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: AssetCategoryCreate) -> AssetCategory:
        AssetCategoryService._validate_unique_code(db, payload.code)
        row = AssetCategory(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="asset_category", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, category_id: uuid.UUID, payload: AssetCategoryUpdate) -> AssetCategory:
        row = db.get(AssetCategory, category_id)
        if row is None or row.is_deleted:
            raise ApiError("Asset category not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            AssetCategoryService._validate_unique_code(db, data["code"])
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="asset_category", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, category_id: uuid.UUID) -> None:
        row = db.get(AssetCategory, category_id)
        if row is None or row.is_deleted:
            raise ApiError("Asset category not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="asset_category", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(AssetCategory.id).where(AssetCategory.code == code, AssetCategory.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Asset category code '{code}' is already in use.", code="duplicate_code", status_code=409)


class CostTypeService:
    """Settings > Cost Categories -- pure reference data, mirrors CurrencyService
    minus the unique-code check (CostType has no code field, doc §7.8)."""

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[CostType], int]:
        stmt = select(CostType).where(CostType.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(CostType.type.ilike(f"%{params.q}%") | CostType.subtype.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, CostType, params.filter_model)
        col = _sort_col(CostType, params.sort_by, CostType.type)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, cost_type_id: uuid.UUID) -> CostType:
        row = db.get(CostType, cost_type_id)
        if row is None or row.is_deleted:
            raise ApiError("Cost type not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: CostTypeCreate) -> CostType:
        row = CostType(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="cost_type", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, cost_type_id: uuid.UUID, payload: CostTypeUpdate) -> CostType:
        row = db.get(CostType, cost_type_id)
        if row is None or row.is_deleted:
            raise ApiError("Cost type not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="cost_type", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, cost_type_id: uuid.UUID) -> None:
        row = db.get(CostType, cost_type_id)
        if row is None or row.is_deleted:
            raise ApiError("Cost type not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="cost_type", entity_id=row.id, action="delete")
        db.commit()
