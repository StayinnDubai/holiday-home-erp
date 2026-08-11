import uuid
from datetime import date
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.foundation import Attachment
from app.schemas.foundation import AttachmentUpdate

# v1 has no virus-scanning engine (plan §8) -- only a content-type/size allowlist.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


class AttachmentService:
    @staticmethod
    def save(
        db: Session,
        *,
        file: UploadFile,
        content: bytes,
        entity_type: str,
        entity_id: uuid.UUID,
        document_name: str | None = None,
        document_type: str | None = None,
        issue_date: date | None = None,
        expiry_date: date | None = None,
    ) -> Attachment:
        from app.core.errors import ApiError

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ApiError(f"Unsupported file type: {file.content_type}", code="unsupported_file_type")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ApiError("File exceeds the 25MB upload limit.", code="file_too_large")

        upload_root = Path(settings.upload_dir) / entity_type
        upload_root.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4()}_{file.filename}"
        dest = upload_root / stored_name
        dest.write_bytes(content)

        attachment = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            file_path=str(dest),
            original_filename=file.filename or stored_name,
            document_name=document_name or file.filename or stored_name,
            content_type=file.content_type,
            document_type=document_type,
            issue_date=issue_date,
            expiry_date=expiry_date,
        )
        db.add(attachment)
        db.flush()
        return attachment

    @staticmethod
    def update(db: Session, attachment_id: uuid.UUID, payload: AttachmentUpdate) -> Attachment:
        from app.core.errors import ApiError

        row = db.get(Attachment, attachment_id)
        if row is None:
            raise ApiError("Attachment not found.", code="not_found", status_code=404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        db.commit()
        db.refresh(row)
        return row
