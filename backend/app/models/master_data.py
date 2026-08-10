"""Master data (plan §3.2), scoped for this pass to exactly the three modules being
built end-to-end: Building, Counterparty (landlords), Unit, and the join table between
them. Everything else in the original plan's master-data section (unit spaces,
ownership shares/effective-dating, handover inspections, etc.) is deferred until its
own module is built -- this is deliberately the header-only slice.
"""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base


class Building(AuditableRecord, Base):
    """Plan §3.2 `building` -- header fields only. A building holds one-or-more units
    (the reverse of Unit.building_id being mandatory and singular)."""

    __tablename__ = "building"

    name: Mapped[str] = mapped_column(String(255))
    developer: Mapped[str | None] = mapped_column(String(255))
    community: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    makani: Mapped[str | None] = mapped_column(String(50))
    floors: Mapped[int | None]
    year_built: Mapped[int | None]
    short_term_permitted: Mapped[str] = mapped_column(String(20), default="yes")  # yes | no | conditional

    units: Mapped[list["Unit"]] = relationship(back_populates="building")


class Counterparty(AuditableRecord, Base):
    """Plan §3.2 `counterparty` (doc §2.6) -- single master for landlord/tenant/
    supplier/agent/OTA. `roles` is stored as a comma-separated string in this pass
    rather than a normalized roles table -- cheap now, easy to split later."""

    __tablename__ = "counterparty"

    code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20))  # individual | company
    roles: Mapped[str | None] = mapped_column(String(255))
    trn: Mapped[str | None] = mapped_column(String(50))
    emirates_id: Mapped[str | None] = mapped_column(String(50))
    hold_flag: Mapped[bool] = mapped_column(default=False)

    unit_links: Mapped[list["UnitLandlord"]] = relationship(back_populates="landlord")


class Unit(AuditableRecord, Base):
    """Plan §3.2 `unit` -- header fields only. Exactly one building (mandatory FK);
    one-or-more landlords via `UnitLandlord` (doc §1.1: a unit may have several
    co-owners). `unit_code` is server-generated (NumberingService), never client-set."""

    __tablename__ = "unit"

    unit_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    unit_name: Mapped[str] = mapped_column(String(255))
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"), nullable=False)
    type: Mapped[str | None] = mapped_column(String(20))
    bathrooms: Mapped[int | None]
    max_occupancy: Mapped[int | None]
    area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))
    status: Mapped[str] = mapped_column(String(20), default="active")
    handover_date: Mapped[date | None] = mapped_column(Date)
    first_live_date: Mapped[date | None] = mapped_column(Date)

    building: Mapped[Building] = relationship(back_populates="units")
    landlord_links: Mapped[list["UnitLandlord"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class UnitLandlord(Base):
    """Many-to-many join, unit <-> landlord (doc §1.1 "a unit may be held by several
    landlords"). No soft-delete/timestamps -- this pass keeps it a plain link row;
    ownership share % and effective-dating (plan's original `UnitOwnership`) are
    deferred until Model B / investor reporting actually needs them."""

    __tablename__ = "unit_landlord"
    __table_args__ = (UniqueConstraint("unit_id", "landlord_id", name="uq_unit_landlord"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit.id"), nullable=False)
    landlord_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)

    unit: Mapped[Unit] = relationship(back_populates="landlord_links")
    landlord: Mapped[Counterparty] = relationship(back_populates="unit_links")
