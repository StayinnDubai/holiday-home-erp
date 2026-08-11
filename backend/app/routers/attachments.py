import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.models.foundation import Attachment
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import AttachmentOut, AttachmentUpdate
from app.services.attachments import AttachmentService

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("", response_model=ListResponse[AttachmentOut])
def list_attachments(entity_type: str, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = (
        select(Attachment)
        .where(Attachment.entity_type == entity_type, Attachment.entity_id == entity_id)
        .order_by(Attachment.created_at.desc())
    )
    rows = list(db.scalars(stmt).all())
    return ListResponse(data=rows, meta=ListMeta(page=1, page_size=len(rows) or 1, total=len(rows)))


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
