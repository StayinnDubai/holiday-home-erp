from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.foundation import Entity
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
        return row

    @staticmethod
    def update(db: Session, payload: EntityUpdate) -> Entity:
        row = CompanyService.get(db)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="entity", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row
