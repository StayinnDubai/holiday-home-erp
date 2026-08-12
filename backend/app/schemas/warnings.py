import uuid

from pydantic import BaseModel


class Warning(BaseModel):
    category: str
    severity: str  # info | warning | critical
    message: str
    entity_type: str
    entity_id: uuid.UUID | None


class WarningsOut(BaseModel):
    items: list[Warning]
    counts: dict[str, int]
    total: int
