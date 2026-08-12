import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Company (doc §7 "Company") -- singleton, GET/PATCH only ----------
class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    legal_name: str
    brand_name: str | None = None
    trn: str | None = None
    vat_number: str | None = None
    license_number: str | None = None
    website: str | None = None
    phone_number: str | None = None
    manager_name: str | None = None
    date_of_registration: date | None = None
    shareholders: str | None = None
    address: str | None = None
    financial_year_start_month: int
    base_currency_id: uuid.UUID
    base_currency_name: str | None = None
    timezone: str


class EntityUpdate(BaseModel):
    legal_name: str | None = None
    brand_name: str | None = None
    trn: str | None = None
    vat_number: str | None = None
    license_number: str | None = None
    website: str | None = None
    phone_number: str | None = None
    manager_name: str | None = None
    date_of_registration: date | None = None
    shareholders: str | None = None
    address: str | None = None
    financial_year_start_month: int | None = None
    base_currency_id: uuid.UUID | None = None
    timezone: str | None = None


# ---------- Currencies (Settings > Currencies) ----------
class CurrencyBase(BaseModel):
    code: str = Field(pattern=r"^\d{3}$")  # manually entered, exactly 3 digits, unique
    name: str
    full_name: str
    # Spot rate to the company's base currency -- None means "not configured yet",
    # display/foundation only (v1's GL stays single-currency, see Currency model doc).
    rate_to_base: float | None = None


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    code: str | None = Field(default=None, pattern=r"^\d{3}$")
    name: str | None = None
    full_name: str | None = None
    rate_to_base: float | None = None


class CurrencyOut(CurrencyBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Tax codes (Settings > Tax Codes, doc §5.7) ----------
class TaxCodeBase(BaseModel):
    code: str
    name: str
    rate: float = 0
    treatment: str = "standard"  # standard | exempt | zero | reverse_charge
    effective_from: date | None = None
    effective_to: date | None = None


class TaxCodeCreate(TaxCodeBase):
    pass


class TaxCodeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    rate: float | None = None
    treatment: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class TaxCodeOut(TaxCodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Asset categories (Settings > Asset Categories) ----------
class AssetCategoryBase(BaseModel):
    code: str
    name: str
    useful_life_months: int | None = None
    method: str = "linear"  # linear | reducing_balance | sum_of_years | custom
    residual_pct: float | None = None
    active: bool = True


class AssetCategoryCreate(AssetCategoryBase):
    pass


class AssetCategoryUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    useful_life_months: int | None = None
    method: str | None = None
    residual_pct: float | None = None
    active: bool | None = None


class AssetCategoryOut(AssetCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Cost types (Settings > Cost Categories) ----------
class CostTypeBase(BaseModel):
    type: str
    subtype: str | None = None
    direct_or_overhead: str = "direct"  # direct | overhead
    recurring: bool = False
    active: bool = True


class CostTypeCreate(CostTypeBase):
    pass


class CostTypeUpdate(BaseModel):
    type: str | None = None
    subtype: str | None = None
    direct_or_overhead: str | None = None
    recurring: bool | None = None
    active: bool | None = None


class CostTypeOut(CostTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Reference list items (doc §7.4) ----------
class ReferenceListItemBase(BaseModel):
    list_name: str
    code: str
    label: str
    is_available: bool | None = None
    sort_order: int = 0
    active: bool = True


class ReferenceListItemCreate(ReferenceListItemBase):
    pass


class ReferenceListItemUpdate(BaseModel):
    label: str | None = None
    is_available: bool | None = None
    sort_order: int | None = None
    active: bool | None = None


class ReferenceListItemOut(ReferenceListItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Settings (key/value config, doc: "never hard-coded") ----------
class SettingBase(BaseModel):
    key: str
    value: str
    description: str | None = None


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: str


class SettingOut(SettingBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------- Attachments (doc §5.3) ----------
class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    file_path: str
    original_filename: str
    document_name: str | None
    content_type: str | None
    document_type: str | None
    issue_date: date | None
    expiry_date: date | None
    created_at: datetime


class AttachmentUpdate(BaseModel):
    document_name: str | None = None
    document_type: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None


# ---------- Comments (doc §1.1: "why", separate from the audit trail) ----------
class CommentCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    author_name: str
    text: str


class CommentOut(CommentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime


# ---------- Audit log (doc §5.2, read-only) ----------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    field: str | None
    old_value: str | None
    new_value: str | None
    action: str
    reason: str | None
    changed_by: str | None
    changed_at: datetime
