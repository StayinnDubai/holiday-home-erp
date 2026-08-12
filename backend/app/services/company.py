from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.foundation import Currency, Entity
from app.schemas.foundation import EntityUpdate
from app.services.audit import AuditService


class CompanyService:
    """Settings > Company (doc §7) -- singleton, exactly one row (D-1). No create/
    delete: the row is guaranteed to exist by app.seed.run, which every environment
    runs once during setup.
    """

    @staticmethod
    def get(db: Session) -> Entity:
        row = db.scalar(select(Entity))
        if row is None:
            raise ApiError(
                "No company record exists yet -- run the seed script (python -m app.seed.run).",
                code="not_found",
                status_code=404,
            )
        CompanyService._attach_relations(db, row)
        return row

    @staticmethod
    def update(db: Session, payload: EntityUpdate) -> Entity:
        row = CompanyService.get(db)
        data = payload.model_dump(exclude_unset=True)
        if data.get("base_currency_id") is not None:
            currency = db.get(Currency, data["base_currency_id"])
            if currency is None or currency.is_deleted:
                raise ApiError("Selected currency does not exist.", code="invalid_reference", status_code=400)
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="entity", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        CompanyService._attach_relations(db, row)
        return row

    @staticmethod
    def _attach_relations(db: Session, row: Entity) -> None:
        currency = db.get(Currency, row.base_currency_id)
        row.base_currency_name = currency.name if currency else None
