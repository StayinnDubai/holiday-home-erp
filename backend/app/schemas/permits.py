import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class DtcmPermitBase(BaseModel):
    permit_number: str
    unit_id: uuid.UUID
    contract_id: uuid.UUID | None = None

    dtcm_unit_unique_code: str | None = None
    operator_name: str | None = None
    operator_license_number: str | None = None
    operator_license_expiry_date: date | None = None
    operator_location: str | None = None
    operator_contact_details: str | None = None

    area: str | None = None
    unit_type: str | None = None
    building_name: str | None = None
    bedrooms: int | None = None
    street_name: str | None = None
    unit_number: str | None = None
    street_number: str | None = None
    dewa_number: str | None = None

    lease_start_date: date | None = None
    lease_expiry_date: date | None = None
    plot_number: str | None = None
    unit_category: str | None = None

    issue_date: date | None = None
    expiry_date: date | None = None
    fee: float | None = None
    status: str = "active"  # active | expired | cancelled


class DtcmPermitCreate(DtcmPermitBase):
    pass


class DtcmPermitUpdate(BaseModel):
    permit_number: str | None = None
    unit_id: uuid.UUID | None = None
    contract_id: uuid.UUID | None = None

    dtcm_unit_unique_code: str | None = None
    operator_name: str | None = None
    operator_license_number: str | None = None
    operator_license_expiry_date: date | None = None
    operator_location: str | None = None
    operator_contact_details: str | None = None

    area: str | None = None
    unit_type: str | None = None
    building_name: str | None = None
    bedrooms: int | None = None
    street_name: str | None = None
    unit_number: str | None = None
    street_number: str | None = None
    dewa_number: str | None = None

    lease_start_date: date | None = None
    lease_expiry_date: date | None = None
    plot_number: str | None = None
    unit_category: str | None = None

    issue_date: date | None = None
    expiry_date: date | None = None
    fee: float | None = None
    status: str | None = None


class DtcmPermitOut(DtcmPermitBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    unit_code: str | None = None
    contract_number: str | None = None
