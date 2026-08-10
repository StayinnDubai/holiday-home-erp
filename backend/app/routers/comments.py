import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.foundation import Comment
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import CommentCreate, CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("", response_model=ListResponse[CommentOut])
def list_comments(entity_type: str, entity_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = (
        select(Comment)
        .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
        .order_by(Comment.created_at.desc())
    )
    rows = list(db.scalars(stmt).all())
    return ListResponse(data=rows, meta=ListMeta(page=1, page_size=len(rows) or 1, total=len(rows)))


@router.post("", response_model=ItemResponse[CommentOut], status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db)):
    comment = Comment(**payload.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return ItemResponse(data=comment)
