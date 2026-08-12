from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate, pagination_params
from app.models.foundation import ReferenceListItem
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import ReferenceListItemCreate, ReferenceListItemOut, ReferenceListItemUpdate

router = APIRouter(prefix="/reference-lists", tags=["reference-lists"])


@router.get("", response_model=ListResponse[ReferenceListItemOut])
def list_reference_items(
    list_name: str | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    stmt = select(ReferenceListItem).where(ReferenceListItem.is_deleted.is_(False))
    if list_name:
        stmt = stmt.where(ReferenceListItem.list_name == list_name)
    stmt = apply_filters(stmt, ReferenceListItem, params.filter_model)
    if params.sort_by and hasattr(ReferenceListItem, params.sort_by):
        col = getattr(ReferenceListItem, params.sort_by)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
    else:
        stmt = stmt.order_by(ReferenceListItem.list_name, ReferenceListItem.sort_order)
    rows, total = paginate(db, stmt, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.post("", response_model=ItemResponse[ReferenceListItemOut], status_code=201)
def create_reference_item(payload: ReferenceListItemCreate, db: Session = Depends(get_db)):
    item = ReferenceListItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return ItemResponse(data=item)


@router.patch("/{item_id}", response_model=ItemResponse[ReferenceListItemOut])
def update_reference_item(item_id: str, payload: ReferenceListItemUpdate, db: Session = Depends(get_db)):
    item = db.get(ReferenceListItem, item_id)
    if item is None or item.is_deleted:
        raise ApiError("Reference list item not found.", code="not_found", status_code=404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return ItemResponse(data=item)


@router.delete("/{item_id}", status_code=204)
def deactivate_reference_item(item_id: str, db: Session = Depends(get_db)):
    """Soft delete (plan §2): reference values are never hard-deleted since other
    tables may still reference the code historically."""
    item = db.get(ReferenceListItem, item_id)
    if item is None or item.is_deleted:
        raise ApiError("Reference list item not found.", code="not_found", status_code=404)
    item.is_deleted = True
    item.active = False
    db.commit()
