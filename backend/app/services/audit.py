import uuid

from sqlalchemy.orm import Session

from app.models.foundation import AuditLog


class AuditService:
    """Writes to the immutable audit_log (doc §5.2). Called explicitly from service-layer
    methods (not DB triggers) so business context -- e.g. why a unit's status changed --
    can be captured alongside the field-level diff. `changed_by` is left None until auth
    exists (plan §7); the column is there so nothing needs to change shape later.
    """

    @staticmethod
    def log(
        db: Session,
        *,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        field: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        reason: str | None = None,
        changed_by: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field=field,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            changed_by=changed_by,
        )
        db.add(entry)
        db.flush()
        return entry
