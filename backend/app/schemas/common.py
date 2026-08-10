from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ListMeta(BaseModel):
    page: int
    page_size: int
    total: int


class ListResponse(BaseModel, Generic[T]):
    """Standard list envelope (plan §4): {data: [...], meta: {page, page_size, total}}."""

    data: list[T]
    meta: ListMeta


class ItemResponse(BaseModel, Generic[T]):
    """Standard single-resource envelope (plan §4): {data: {...}}."""

    data: T
