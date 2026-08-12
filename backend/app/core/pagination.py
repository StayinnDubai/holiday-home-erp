import json
from dataclasses import dataclass, field

from fastapi import Query
from sqlalchemy import Date, Select, and_, cast, func, or_, select
from sqlalchemy.orm import Session


@dataclass
class PaginationParams:
    """Shared list-endpoint contract (plan §4 / §6): every list endpoint takes the
    same page/page_size/sort/search/filter params, matching what ag-Grid's infinite
    row model sends from the frontend.
    """

    page: int = 1
    page_size: int = 25
    sort_by: str | None = None
    sort_dir: str = "asc"
    q: str | None = None
    # ag-Grid's filterModel, one entry per filtered column: {"<colId>": {...}}. See
    # `apply_filters` below for the per-column shape.
    filter_model: dict | None = field(default=None)


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    q: str | None = Query(None),
    filter_model: str | None = Query(None),
) -> PaginationParams:
    parsed_filter_model = None
    if filter_model:
        try:
            parsed_filter_model = json.loads(filter_model)
        except ValueError:
            parsed_filter_model = None
    return PaginationParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir, q=q, filter_model=parsed_filter_model
    )


def paginate(db: Session, stmt: Select, params: PaginationParams) -> tuple[list, int]:
    """Runs a count + a page of results for the given base select statement."""
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page_stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
    rows = list(db.scalars(page_stmt).all())
    return rows, total


def _text_condition(col, cond: dict):
    ctype = cond.get("type")
    val = cond.get("filter")
    if ctype == "contains":
        return col.ilike(f"%{val}%")
    if ctype == "notContains":
        return ~col.ilike(f"%{val}%")
    if ctype == "equals":
        return col == val
    if ctype == "notEqual":
        return col != val
    if ctype == "startsWith":
        return col.ilike(f"{val}%")
    if ctype == "endsWith":
        return col.ilike(f"%{val}")
    if ctype == "blank":
        return col.is_(None)
    if ctype == "notBlank":
        return col.isnot(None)
    return None


def _number_condition(col, cond: dict):
    ctype = cond.get("type")
    val = cond.get("filter")
    val_to = cond.get("filterTo")
    if ctype == "equals":
        return col == val
    if ctype == "notEqual":
        return col != val
    if ctype == "greaterThan":
        return col > val
    if ctype == "greaterThanOrEqual":
        return col >= val
    if ctype == "lessThan":
        return col < val
    if ctype == "lessThanOrEqual":
        return col <= val
    if ctype == "inRange":
        return col.between(val, val_to)
    if ctype == "blank":
        return col.is_(None)
    if ctype == "notBlank":
        return col.isnot(None)
    return None


def _date_condition(col, cond: dict):
    ctype = cond.get("type")
    # ag-Grid sends "YYYY-MM-DD HH:MM:SS" for date filters -- our date columns only
    # need the first 10 characters. Explicitly cast the literal to DATE rather than
    # relying on `col`'s type to coerce it -- that inference doesn't happen for a
    # `cast(jsonb_expr, Date)` column (Postgres then sees `date = varchar` and
    # errors), only for a plain mapped Date column, so it has to be forced here for
    # both to work uniformly.
    date_from = (cond.get("dateFrom") or "")[:10] or None
    date_to = (cond.get("dateTo") or "")[:10] or None
    date_from_c = cast(date_from, Date) if date_from else None
    date_to_c = cast(date_to, Date) if date_to else None
    if ctype == "equals":
        return col == date_from_c
    if ctype == "notEqual":
        return col != date_from_c
    if ctype == "greaterThan":
        return col > date_from_c
    if ctype == "lessThan":
        return col < date_from_c
    if ctype == "inRange":
        return col.between(date_from_c, date_to_c)
    if ctype == "blank":
        return col.is_(None)
    if ctype == "notBlank":
        return col.isnot(None)
    return None


def _condition(col, filter_type: str | None, cond: dict):
    if filter_type == "text":
        return _text_condition(col, cond)
    if filter_type == "number":
        return _number_condition(col, cond)
    if filter_type == "date":
        return _date_condition(col, cond)
    return None


def apply_filters(stmt: Select, model, filter_model: dict | None, extra_columns: dict | None = None) -> Select:
    """Applies ag-Grid's per-column filterModel to `stmt`, entirely by reflection --
    `getattr(model, field)` finds the matching real column for any resource without
    per-service code, mirroring how `_sort_col` already resolves sort_by generically.

    Only works for *real* columns on `model`. Computed/joined display columns (e.g.
    a `group_name` resolved via a join) aren't attributes of `model` and so are
    silently skipped here -- same reasoning as sorting's `sortable: false` gate:
    callers pass `extra_columns` (a `{colId: SQLAlchemy column}` map, typically the
    already-joined column from that service's sort-by branch) to support filtering
    those specific fields too, and the frontend only offers the filter UI for
    columns one of the two paths can actually satisfy (entity-page.component.ts /
    the bank-statement components gate `filter` the same way they gate `sortable`).
    """
    if not filter_model:
        return stmt
    extra_columns = extra_columns or {}
    for colid, cond in filter_model.items():
        col = extra_columns.get(colid)
        if col is None:
            col = getattr(model, colid, None)
        if col is None:
            continue

        conditions = cond.get("conditions")
        if conditions:
            operator = cond.get("operator", "AND")
            clauses = [c for c in (_condition(col, sub.get("filterType"), sub) for sub in conditions) if c is not None]
            if not clauses:
                continue
            stmt = stmt.where(or_(*clauses) if operator == "OR" else and_(*clauses))
        else:
            clause = _condition(col, cond.get("filterType"), cond)
            if clause is not None:
                stmt = stmt.where(clause)
    return stmt
