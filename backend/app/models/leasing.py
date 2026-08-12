"""Tenancy Contracts / Ejari (doc §1.4) -- the inbound lease, company <- landlord.
Its outbound counterpart (Rental Agreement, doc §1.6) is a separate, later module.

Scoped like master_data.py: header-only slice, plus the two child objects the doc
treats as first-class -- contract parties and the Ejari registration record. The
POA object (`ContractPOA`) and the payment-schedule/cheque-generation workflow are
deferred until the Accounting-core milestone exists (a payment schedule only means
something once there's a cheque ledger to post it to) -- see doc §1.4 "Functionality".
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base


class TenancyContract(AuditableRecord, Base):
    """doc §1.4 "Contract" object. One contract covers exactly one unit (Q178);
    co-ownership is still possible via TenancyContractParty -- that's ownership,
    not contract scope. Renewal is a new row (`renewal_of_id` -> predecessor),
    never an edit to an existing contract's term (doc "Renewal creates a new
    contract, never an amendment", Q151)."""

    __tablename__ = "tenancy_contract"

    contract_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit.id"), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(20), default="new")  # new | renewal
    renewal_of_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenancy_contract.id"))

    contract_date: Mapped[date | None] = mapped_column(Date)  # date the contract itself is dated/signed
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    total_annual_rent: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    instalment_count: Mapped[int] = mapped_column(default=1)
    payment_method: Mapped[str] = mapped_column(String(20), default="cheque")  # cheque | transfer

    # Grace period (doc §1.4 point 2, "as-incurred zero-cost months" -- on the
    # contract itself; EjariRegistration carries its own copy verbatim as registered).
    grace_period_start_date: Mapped[date | None] = mapped_column(Date)
    grace_period_end_date: Mapped[date | None] = mapped_column(Date)

    security_deposit_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    agency_name: Mapped[str | None] = mapped_column(String(255))
    agency_fee_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    agency_fee_vat_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    agency_renewal_charge_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))

    landlord_maintenance_threshold: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))

    notice_period_days: Mapped[int | None]
    vacating_notice_period_days: Mapped[int | None]
    renewal_notice_period_days: Mapped[int | None]
    early_termination_notice_days: Mapped[int | None]
    early_termination_penalty_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))

    # Hard gates (doc §1.4 "Landlord permissions"). Enforcement of what they gate
    # (short-term product line / DTCM permits / rental agreements) lands with those
    # later modules -- the flags are captured here now so nothing has to be
    # retrofitted onto this contract once they exist.
    sublease_permitted: Mapped[str] = mapped_column(String(10), default="no")  # yes | no
    holiday_home_permitted: Mapped[str] = mapped_column(String(10), default="no")  # yes | no

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|active|expired|terminated|superseded

    # Lease daily calculation / ledger registration. When True, activating this
    # contract (status -> 'active') generates a schedule of draft Bills against the
    # landlord (services/rent_schedule.py) -- daily_rate = total_annual_rent / 365,
    # split into `instalment_count` periods, reduced by any TenancyContractAdjustment
    # rows. `rent_schedule_generated` guards it from firing twice -- the term is
    # locked once active (LOCKED_FIELDS_WHEN_ACTIVE below) so a schedule computed at
    # activation stays valid for the life of the contract.
    auto_calculate_rent: Mapped[bool] = mapped_column(Boolean, default=False)
    rent_schedule_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    renewal_of: Mapped["TenancyContract | None"] = relationship(remote_side="TenancyContract.id")
    parties: Mapped[list["TenancyContractParty"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )


class TenancyContractParty(Base):
    """doc §1.4 "Contract party" -- one per landlord on the contract. Share % and
    payee/role distinction are intentionally not carried here yet, the same
    simplification master_data.py already makes for `UnitLandlord`: cheap to add
    once Model B / payment-schedule generation actually needs them, not before."""

    __tablename__ = "tenancy_contract_party"
    __table_args__ = (UniqueConstraint("contract_id", "landlord_id", name="uq_tenancy_contract_party"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy_contract.id"), nullable=False)
    landlord_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)

    contract: Mapped[TenancyContract] = relationship(back_populates="parties")


class EjariRegistration(AuditableRecord, Base):
    """doc §1.4 `EjariRegistration` -- a transcription of the certificate exactly as
    registered, stored verbatim even where it duplicates or contradicts the contract.
    Design principle from the doc: "nothing here overwrites anything, and nothing is
    auto-derived" -- divergence from the contract is itself information, surfaced by
    the variance check in the service layer rather than corrected. One per contract
    (Q183), enforced by the unique constraint below."""

    __tablename__ = "ejari_registration"
    __table_args__ = (UniqueConstraint("contract_id", name="uq_ejari_registration_contract"),)

    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy_contract.id"), nullable=False)

    # Registration
    ejari_contract_number: Mapped[str | None] = mapped_column(String(50))
    registration_date: Mapped[date | None] = mapped_column(Date)
    receipt_number: Mapped[str | None] = mapped_column(String(50))
    total_fees: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))

    # Term
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    grace_start_date: Mapped[date | None] = mapped_column(Date)
    grace_end_date: Mapped[date | None] = mapped_column(Date)

    # Amounts -- "Actual" is net of any discount and is what drives accounting (doc §1.4 point 1)
    contract_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    annual_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    actual_contract_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    actual_annual_amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    discount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    security_deposit: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))

    # Owner
    owner_number: Mapped[str | None] = mapped_column(String(50))
    owner_nationality: Mapped[str | None] = mapped_column(String(100))

    # Tenant -- your own company on an inbound registration (doc §1.4 point 4)
    tenant_name: Mapped[str | None] = mapped_column(String(255))
    tenant_no: Mapped[str | None] = mapped_column(String(50))
    license_number: Mapped[str | None] = mapped_column(String(50))
    license_expiry: Mapped[date | None] = mapped_column(Date)
    license_issuer: Mapped[str | None] = mapped_column(String(100))
    tel_no: Mapped[str | None] = mapped_column(String(50))
    fax_no: Mapped[str | None] = mapped_column(String(50))

    # Property
    building_name_no: Mapped[str | None] = mapped_column(String(255))
    property_no: Mapped[str | None] = mapped_column(String(100))
    makani_no: Mapped[str | None] = mapped_column(String(50))
    plot_number: Mapped[str | None] = mapped_column(String(50))
    land_dm_no: Mapped[str | None] = mapped_column(String(50))
    land_area: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))
    dewa_premise_no: Mapped[str | None] = mapped_column(String(50))

    # Classification
    classification_type: Mapped[str | None] = mapped_column(String(100))
    classification_subtype: Mapped[str | None] = mapped_column(String(100))
    usage: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))

    status: Mapped[str] = mapped_column(String(20), default="active")  # active | expired | superseded

    contract: Mapped[TenancyContract] = relationship()


class TenancyContractAdjustment(AuditableRecord, Base):
    """Discount / grace period / other compensation given by the landlord during a
    tenancy contract -- read by services/rent_schedule.py when computing each
    generated Bill's amount (a `grace_period` zeroes its overlapping days, a
    `discount` reduces them by `discount_pct`, a `compensation` is a flat one-time
    deduction from the period containing `start_date`). Distinct from the single
    `grace_period_start_date`/`end_date` pair on TenancyContract itself, which stays
    purely documentary (the contract's own stated terms) -- this table is the
    operational record multiple such events actually get entered against."""

    __tablename__ = "tenancy_contract_adjustment"

    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy_contract.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20))  # discount | grace_period | compensation
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    discount_pct: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    amount: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    reason: Mapped[str | None] = mapped_column(Text)

    contract: Mapped[TenancyContract] = relationship()
