from dataclasses import dataclass

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


@dataclass
class PaginationParams:
    """Shared list-endpoint contract (plan §4 / §6): every list endpoint takes the
    same page/page_size/sort/search params, matching what ag-Grid's server-side
    row model sends from the frontend.
    """

    page: int = 1
    page_size: int = 25
    sort_by: str | None = None
    sort_dir: str = "asc"
    q: str | None = None


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    q: str | None = Query(None),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir, q=q)


def paginate(db: Session, stmt: Select, params: PaginationParams) -> tuple[list, int]:
    """Runs a count + a page of results for the given base select statement."""
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page_stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    rows = list(db.scalars(page_stmt).all())
    return rows, total
