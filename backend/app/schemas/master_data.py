import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


# ---------- Building ----------
class BuildingBase(BaseModel):
    name: str
    developer: str | None = None
    community: str | None = None
    address: str | None = None
    makani: str | None = None
    floors: int | None = None
    year_built: int | None = None
    short_term_permitted: str = "yes"  # yes | no | conditional


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: str | None = None
    developer: str | None = None
    community: str | None = None
    address: str | None = None
    makani: str | None = None
    floors: int | None = None
    year_built: int | None = None
    short_term_permitted: str | None = None


class BuildingOut(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    unit_count: int = 0


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
