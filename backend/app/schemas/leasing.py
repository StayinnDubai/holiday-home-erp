import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


# ---------- Tenancy Contract ----------
class TenancyContractBase(BaseModel):
    unit_id: uuid.UUID
    landlord_ids: list[uuid.UUID] = Field(default_factory=list)
    contract_type: str = "new"  # new | renewal
    renewal_of_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    total_annual_rent: float
    instalment_count: int = 1
    payment_method: str = "cheque"  # cheque | transfer
    security_deposit_amount: float | None = None
    agency_fee_amount: float | None = None
    agency_fee_vat_applicable: bool = True
    notice_period_days: int | None = None
    sublease_permitted: str = "no"  # yes | no
    holiday_home_permitted: str = "no"  # yes | no
    status: str = "draft"  # draft | active | expired | terminated | superseded


class TenancyContractCreate(TenancyContractBase):
    pass


class TenancyContractUpdate(BaseModel):
    unit_id: uuid.UUID | None = None
    landlord_ids: list[uuid.UUID] | None = None
    contract_type: str | None = None
    renewal_of_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    total_annual_rent: float | None = None
    instalment_count: int | None = None
    payment_method: str | None = None
    security_deposit_amount: float | None = None
    agency_fee_amount: float | None = None
    agency_fee_vat_applicable: bool | None = None
    notice_period_days: int | None = None
    sublease_permitted: str | None = None
    holiday_home_permitted: str | None = None
    status: str | None = None


class TenancyContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_number: str
    unit_id: uuid.UUID
    unit_code: str | None = None
    unit_name: str | None = None
    landlord_ids: list[uuid.UUID] = Field(default_factory=list)
    landlord_names: str | None = None
    contract_type: str
    renewal_of_id: uuid.UUID | None = None
    renewal_of_contract_number: str | None = None
    renewed_by_id: uuid.UUID | None = None
    renewed_by_contract_number: str | None = None
    # doc §1.4 "Gap detection": positive only if the new contract starts after the
    # predecessor's end date -- an uncovered period, surfaced, never auto-corrected.
    gap_days: int | None = None
    start_date: date
    end_date: date
    total_annual_rent: float
    instalment_count: int
    payment_method: str
    security_deposit_amount: float | None = None
    agency_fee_amount: float | None = None
    agency_fee_vat_applicable: bool
    notice_period_days: int | None = None
    sublease_permitted: str
    holiday_home_permitted: str
    status: str


# ---------- Ejari Registration ----------
class EjariRegistrationBase(BaseModel):
    contract_id: uuid.UUID

    ejari_contract_number: str | None = None
    registration_date: date | None = None
    receipt_number: str | None = None
    total_fees: float | None = None

    start_date: date | None = None
    end_date: date | None = None
    grace_start_date: date | None = None
    grace_end_date: date | None = None

    contract_amount: float | None = None
    annual_amount: float | None = None
    actual_contract_amount: float | None = None
    actual_annual_amount: float | None = None
    discount: float | None = None
    security_deposit: float | None = None

    owner_number: str | None = None
    owner_nationality: str | None = None

    tenant_name: str | None = None
    tenant_no: str | None = None
    license_number: str | None = None
    license_expiry: date | None = None
    license_issuer: str | None = None
    tel_no: str | None = None
    fax_no: str | None = None

    building_name_no: str | None = None
    property_no: str | None = None
    makani_no: str | None = None
    plot_number: str | None = None
    land_dm_no: str | None = None
    land_area: float | None = None
    dewa_premise_no: str | None = None

    classification_type: str | None = None
    classification_subtype: str | None = None
    usage: str | None = None
    size: float | None = None

    status: str = "active"  # active | expired | superseded


class EjariRegistrationCreate(EjariRegistrationBase):
    pass


class EjariRegistrationUpdate(BaseModel):
    contract_id: uuid.UUID | None = None

    ejari_contract_number: str | None = None
    registration_date: date | None = None
    receipt_number: str | None = None
    total_fees: float | None = None

    start_date: date | None = None
    end_date: date | None = None
    grace_start_date: date | None = None
    grace_end_date: date | None = None

    contract_amount: float | None = None
    annual_amount: float | None = None
    actual_contract_amount: float | None = None
    actual_annual_amount: float | None = None
    discount: float | None = None
    security_deposit: float | None = None

    owner_number: str | None = None
    owner_nationality: str | None = None

    tenant_name: str | None = None
    tenant_no: str | None = None
    license_number: str | None = None
    license_expiry: date | None = None
    license_issuer: str | None = None
    tel_no: str | None = None
    fax_no: str | None = None

    building_name_no: str | None = None
    property_no: str | None = None
    makani_no: str | None = None
    plot_number: str | None = None
    land_dm_no: str | None = None
    land_area: float | None = None
    dewa_premise_no: str | None = None

    classification_type: str | None = None
    classification_subtype: str | None = None
    usage: str | None = None
    size: float | None = None

    status: str | None = None


class EjariRegistrationOut(EjariRegistrationBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_number: str | None = None
    # doc §1.4 "Ejari-versus-contract variance check" -- warned, never blocked.
    variance_warnings: list[str] = Field(default_factory=list)
