import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
    content_type: str | None
    document_type: str | None
    issue_date: date | None
    expiry_date: date | None
    created_at: datetime


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
