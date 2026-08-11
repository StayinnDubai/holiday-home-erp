import uuid
from datetime import date
from datetime import date as _date  # BuildingDeposit has a field literally named
# `date`, which shadows the `date` type inside its own class body -- alias avoids it.

from pydantic import BaseModel, ConfigDict, Field


# ---------- Building ----------
class BuildingBase(BaseModel):
    name: str
    developer: str | None = None
    community: str | None = None
    address: str | None = None
    makani: str | None = None
    plot_number: str | None = None
    floors: int | None = None
    year_built: int | None = None

    short_term_permitted: str = "yes"  # yes | no | conditional
    short_term_conditions: str | None = None
    guest_limit: int | None = None
    minimum_stay_nights: int | None = None
    party_noise_rules: str | None = None
    pet_rules: str | None = None

    access_rules: str | None = None

    move_in_permit_required: bool = False
    move_in_permit_trigger_events: str | None = None
    move_in_permit_lead_time_days: int | None = None
    move_in_permit_cost: float | None = None
    move_in_permit_deposit_amount: float | None = None
    move_in_permit_deposit_refundable: bool | None = None
    move_in_permit_documents_required: str | None = None
    move_in_permit_checklist: str | None = None
    move_in_permit_applied_by: str | None = None
    move_in_permit_turnaround: str | None = None

    parking_allocation_basis: str | None = None
    parking_bays_per_unit: int | None = None
    parking_card_required: bool | None = None
    parking_cost: float | None = None
    visitor_parking_rules: str | None = None

    service_charges_note: str | None = None

    portal_system_name: str | None = None
    portal_username: str | None = None
    portal_reference_number: str | None = None
    portal_notes: str | None = None


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: str | None = None
    developer: str | None = None
    community: str | None = None
    address: str | None = None
    makani: str | None = None
    plot_number: str | None = None
    floors: int | None = None
    year_built: int | None = None

    short_term_permitted: str | None = None
    short_term_conditions: str | None = None
    guest_limit: int | None = None
    minimum_stay_nights: int | None = None
    party_noise_rules: str | None = None
    pet_rules: str | None = None

    access_rules: str | None = None

    move_in_permit_required: bool | None = None
    move_in_permit_trigger_events: str | None = None
    move_in_permit_lead_time_days: int | None = None
    move_in_permit_cost: float | None = None
    move_in_permit_deposit_amount: float | None = None
    move_in_permit_deposit_refundable: bool | None = None
    move_in_permit_documents_required: str | None = None
    move_in_permit_checklist: str | None = None
    move_in_permit_applied_by: str | None = None
    move_in_permit_turnaround: str | None = None

    parking_allocation_basis: str | None = None
    parking_bays_per_unit: int | None = None
    parking_card_required: bool | None = None
    parking_cost: float | None = None
    visitor_parking_rules: str | None = None

    service_charges_note: str | None = None

    portal_system_name: str | None = None
    portal_username: str | None = None
    portal_reference_number: str | None = None
    portal_notes: str | None = None


class BuildingOut(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    unit_count: int = 0


# ---------- Building contacts ----------
class BuildingContactBase(BaseModel):
    building_id: uuid.UUID
    name: str
    role: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    working_hours: str | None = None
    out_of_hours_contact: str | None = None
    notes: str | None = None
    active: bool = True


class BuildingContactCreate(BuildingContactBase):
    pass


class BuildingContactUpdate(BaseModel):
    building_id: uuid.UUID | None = None
    name: str | None = None
    role: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    working_hours: str | None = None
    out_of_hours_contact: str | None = None
    notes: str | None = None
    active: bool | None = None


class BuildingContactOut(BuildingContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    building_name: str | None = None


# ---------- Building amenities ----------
class BuildingAmenityBase(BaseModel):
    building_id: uuid.UUID
    name: str
    operating_hours: str | None = None
    access_method: str | None = None  # card | code | key | open
    booking_required: bool = False
    guest_access_permitted: bool = True
    rules_notes: str | None = None
    active: bool = True


class BuildingAmenityCreate(BuildingAmenityBase):
    pass


class BuildingAmenityUpdate(BaseModel):
    building_id: uuid.UUID | None = None
    name: str | None = None
    operating_hours: str | None = None
    access_method: str | None = None
    booking_required: bool | None = None
    guest_access_permitted: bool | None = None
    rules_notes: str | None = None
    active: bool | None = None


class BuildingAmenityOut(BuildingAmenityBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    building_name: str | None = None


# ---------- Building deposits and fees ----------
class BuildingDepositBase(BaseModel):
    building_id: uuid.UUID
    type: str  # refundable_deposit | non_refundable_fee
    description: str
    amount: float
    date: _date | None = None
    reference: str | None = None
    refundable: bool = False
    condition_for_release: str | None = None
    recovery_status: str = "outstanding"  # outstanding | recovered | forfeited | not_applicable


class BuildingDepositCreate(BuildingDepositBase):
    pass


class BuildingDepositUpdate(BaseModel):
    building_id: uuid.UUID | None = None
    type: str | None = None
    description: str | None = None
    amount: float | None = None
    date: _date | None = None
    reference: str | None = None
    refundable: bool | None = None
    condition_for_release: str | None = None
    recovery_status: str | None = None


class BuildingDepositOut(BuildingDepositBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    building_name: str | None = None


# ---------- Counterparty ----------
class CounterpartyBase(BaseModel):
    code: str | None = None
    name: str
    type: str  # individual | company
    roles: str | None = None
    trn: str | None = None
    emirates_id: str | None = None
    hold_flag: bool = False


class CounterpartyCreate(CounterpartyBase):
    pass


class CounterpartyUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    type: str | None = None
    roles: str | None = None
    trn: str | None = None
    emirates_id: str | None = None
    hold_flag: bool | None = None


class CounterpartyOut(CounterpartyBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    unit_count: int = 0


# ---------- Unit ----------
class UnitBase(BaseModel):
    unit_name: str
    building_id: uuid.UUID
    landlord_ids: list[uuid.UUID] = Field(default_factory=list)
    type: str | None = None
    bathrooms: int | None = None
    max_occupancy: int | None = None
    area_sqft: float | None = None
    status: str = "active"
    handover_date: date | None = None
    first_live_date: date | None = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    unit_name: str | None = None
    building_id: uuid.UUID | None = None
    landlord_ids: list[uuid.UUID] | None = None
    type: str | None = None
    bathrooms: int | None = None
    max_occupancy: int | None = None
    area_sqft: float | None = None
    status: str | None = None
    handover_date: date | None = None
    first_live_date: date | None = None


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    unit_code: str
    unit_name: str
    building_id: uuid.UUID
    building_name: str | None = None
    landlord_ids: list[uuid.UUID] = Field(default_factory=list)
    landlord_names: str | None = None
    type: str | None = None
    bathrooms: int | None = None
    max_occupancy: int | None = None
    area_sqft: float | None = None
    status: str
    handover_date: date | None = None
    first_live_date: date | None = None
