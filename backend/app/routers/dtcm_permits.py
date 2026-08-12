import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.permits import DtcmPermitCreate, DtcmPermitOut, DtcmPermitUpdate
from app.services.permits import DtcmPermitService

router = APIRouter(prefix="/dtcm-permits", tags=["dtcm-permits"])


@router.get("", response_model=ListResponse[DtcmPermitOut])
def list_dtcm_permits(
    unit_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(pagination_params),
):
    rows, total = DtcmPermitService.list_page(db, params, unit_id=unit_id)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{permit_id}", response_model=ItemResponse[DtcmPermitOut])
def get_dtcm_permit(permit_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=DtcmPermitService.get(db, permit_id))


@router.post("", response_model=ItemResponse[DtcmPermitOut], status_code=201)
def create_dtcm_permit(payload: DtcmPermitCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=DtcmPermitService.create(db, payload))


@router.patch("/{permit_id}", response_model=ItemResponse[DtcmPermitOut])
def update_dtcm_permit(permit_id: uuid.UUID, payload: DtcmPermitUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=DtcmPermitService.update(db, permit_id, payload))


@router.delete("/{permit_id}", status_code=204)
def delete_dtcm_permit(permit_id: uuid.UUID, db: Session = Depends(get_db)):
    DtcmPermitService.soft_delete(db, permit_id)
