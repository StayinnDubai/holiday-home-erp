import uuid
from datetime import datetime, date

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IdMixin:
    """UUID primary key, per plan §3 (business keys like unit_code live alongside it,
    never replace it)."""

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Delete is soft by default (plan §2 / doc §5.1) -- rows are archived, never destroyed."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# Every transactional table also carries an `entity_id` FK to `foundation.Entity` (doc D-1),
# defaulted to the single row that exists today even though v1 is single-entity --
# retrofitting it later would be a rewrite, carrying it now is one column. Declared directly
# on each concrete model (not a mixin) to avoid a circular import with foundation.Entity.


class AuditableRecord(IdMixin, TimestampMixin, SoftDeleteMixin):
    """Standard mixin bundle for ordinary business tables (plan §2)."""

    pass


__all__ = [
    "Base",
    "IdMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditableRecord",
    "date",
]
