import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate, pagination_params
from app.models.foundation import Attachment
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import AttachmentOut, AttachmentUpdate
from app.services.attachments import AttachmentService

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("", response_model=ListResponse[AttachmentOut])
def list_attachments(
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    """entity_type/entity_id filter to one record's files (every per-record
    attachments panel does this). Omit both to list every attachment across every
    module -- the Documents register (frontend/src/app/features/documents) does
    this, reusing the same standard PaginationParams contract every other list
    endpoint uses instead of the old unpaginated single-record dump."""
    stmt = select(Attachment)
    if entity_type is not None:
        stmt = stmt.where(Attachment.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(Attachment.entity_id == entity_id)
    if params.q:
        stmt = stmt.where(Attachment.document_name.ilike(f"%{params.q}%"))
    stmt = apply_filters(stmt, Attachment, params.filter_model)
    sort_col = getattr(Attachment, params.sort_by, None) if params.sort_by else None
    sort_col = sort_col if sort_col is not None else Attachment.created_at
    stmt = stmt.order_by(sort_col.desc() if params.sort_dir != "asc" else sort_col.asc())
    rows, total = paginate(db, stmt, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.post("", response_model=ItemResponse[AttachmentOut], status_code=201)
async def upload_attachment(
    entity_type: str = Form(...),
    entity_id: uuid.UUID = Form(...),
    document_name: str | None = Form(None),
    document_type: str | None = Form(None),
    issue_date: date | None = Form(None),
    expiry_date: date | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    attachment = AttachmentService.save(
        db,
        file=file,
        content=content,
        entity_type=entity_type,
        entity_id=entity_id,
        document_name=document_name,
        document_type=document_type,
        issue_date=issue_date,
        expiry_date=expiry_date,
    )
    db.commit()
    db.refresh(attachment)
    return ItemResponse(data=attachment)


@router.patch("/{attachment_id}", response_model=ItemResponse[AttachmentOut])
def update_attachment(attachment_id: uuid.UUID, payload: AttachmentUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=AttachmentService.update(db, attachment_id, payload))


@router.get("/{attachment_id}/file")
def download_attachment(attachment_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(Attachment, attachment_id)
    if row is None:
        raise ApiError("Attachment not found.", code="not_found", status_code=404)
    return FileResponse(
        row.file_path,
        filename=row.original_filename,
        media_type=row.content_type or "application/octet-stream",
    )


@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(Attachment, attachment_id)
    if row is None:
        raise ApiError("Attachment not found.", code="not_found", status_code=404)
    db.delete(row)
    db.commit()
