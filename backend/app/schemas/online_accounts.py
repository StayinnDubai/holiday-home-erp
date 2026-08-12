import uuid

from pydantic import BaseModel, ConfigDict


class OnlineAccountBase(BaseModel):
    service_name: str
    category: str | None = None
    related_to: str | None = None
    url: str | None = None
    username: str | None = None
    password: str | None = None
    sign_in_method: str | None = None  # password | two_factor | sso | api_key | other
    recovery_email: str | None = None
    comments: str | None = None
    active: bool = True


class OnlineAccountCreate(OnlineAccountBase):
    pass


class OnlineAccountUpdate(BaseModel):
    service_name: str | None = None
    category: str | None = None
    related_to: str | None = None
    url: str | None = None
    username: str | None = None
    password: str | None = None
    sign_in_method: str | None = None
    recovery_email: str | None = None
    comments: str | None = None
    active: bool | None = None


class OnlineAccountOut(OnlineAccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
