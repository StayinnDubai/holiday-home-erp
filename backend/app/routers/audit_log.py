import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.foundation import AuditLog
from app.schemas.common import ListMeta, ListResponse
from app.schemas.foundation import AuditLogOut

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("", response_model=ListResponse[AuditLogOut])
def list_audit_log(entity_type: str, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    """Read-only (doc §5.2: immutable, never editable). No write endpoints exist here
    on purpose -- entries are only ever created via AuditService from other services."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.changed_at.desc())
    )
    rows = list(db.scalars(stmt).all())
    return ListResponse(data=rows, meta=ListMeta(page=1, page_size=len(rows) or 1, total=len(rows)))
