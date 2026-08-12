import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.online_accounts import OnlineAccount
from app.schemas.online_accounts import OnlineAccountCreate, OnlineAccountUpdate
from app.services.audit import AuditService


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


class OnlineAccountService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[OnlineAccount], int]:
        stmt = select(OnlineAccount).where(OnlineAccount.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(OnlineAccount.service_name.ilike(f"%{params.q}%") | OnlineAccount.related_to.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, OnlineAccount, params.filter_model)
        col = _sort_col(OnlineAccount, params.sort_by, OnlineAccount.service_name)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, account_id: uuid.UUID) -> OnlineAccount:
        row = db.get(OnlineAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Online account not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: OnlineAccountCreate) -> OnlineAccount:
        row = OnlineAccount(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="online_account", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, account_id: uuid.UUID, payload: OnlineAccountUpdate) -> OnlineAccount:
        row = db.get(OnlineAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Online account not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="online_account", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, account_id: uuid.UUID) -> None:
        row = db.get(OnlineAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Online account not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="online_account", entity_id=row.id, action="delete")
        db.commit()
