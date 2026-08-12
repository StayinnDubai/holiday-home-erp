"""DTCM Permits (doc §1.8) -- the licence that makes a unit legal as a holiday
home. Fields transcribed verbatim from a real DTCM Unit Permit certificate, same
design principle as EjariRegistration (backend/app/models/leasing.py): stored as
printed even where a value could instead be looked up from Unit/Building, since
divergence from those records is itself information, not an error to silently
correct. `unit_id` is the real relation; `contract_id` is optional -- the tenancy
contract in effect when the permit was issued/renewed.
"""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base


class DtcmPermit(AuditableRecord, Base):
    __tablename__ = "dtcm_permit"

    permit_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit.id"), nullable=False)
    contract_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenancy_contract.id"))

    dtcm_unit_unique_code: Mapped[str | None] = mapped_column(String(50))
    operator_name: Mapped[str | None] = mapped_column(String(255))
    operator_license_number: Mapped[str | None] = mapped_column(String(50))
    operator_license_expiry_date: Mapped[date | None] = mapped_column(Date)
    operator_location: Mapped[str | None] = mapped_column(String(255))
    operator_contact_details: Mapped[str | None] = mapped_column(String(255))

    # As printed on the certificate -- may diverge from the linked Unit/Building.
    area: Mapped[str | None] = mapped_column(String(255))
    unit_type: Mapped[str | None] = mapped_column(String(50))
    building_name: Mapped[str | None] = mapped_column(String(255))
    bedrooms: Mapped[int | None]
    street_name: Mapped[str | None] = mapped_column(String(255))
    unit_number: Mapped[str | None] = mapped_column(String(50))
    street_number: Mapped[str | None] = mapped_column(String(50))
    dewa_number: Mapped[str | None] = mapped_column(String(100))

    lease_start_date: Mapped[date | None] = mapped_column(Date)
    lease_expiry_date: Mapped[date | None] = mapped_column(Date)
    plot_number: Mapped[str | None] = mapped_column(String(50))
    unit_category: Mapped[str | None] = mapped_column(String(50))

    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    fee: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | expired | cancelled

    unit: Mapped["Unit"] = relationship()  # noqa: F821
    contract: Mapped["TenancyContract | None"] = relationship()  # noqa: F821
