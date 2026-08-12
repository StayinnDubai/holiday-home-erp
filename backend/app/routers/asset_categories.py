import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.foundation import AssetCategoryCreate, AssetCategoryOut, AssetCategoryUpdate
from app.services.foundation import AssetCategoryService

router = APIRouter(prefix="/asset-categories", tags=["asset-categories"])


@router.get("", response_model=ListResponse[AssetCategoryOut])
def list_asset_categories(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = AssetCategoryService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{category_id}", response_model=ItemResponse[AssetCategoryOut])
def get_asset_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=AssetCategoryService.get(db, category_id))


@router.post("", response_model=ItemResponse[AssetCategoryOut], status_code=201)
def create_asset_category(payload: AssetCategoryCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=AssetCategoryService.create(db, payload))


@router.patch("/{category_id}", response_model=ItemResponse[AssetCategoryOut])
def update_asset_category(category_id: uuid.UUID, payload: AssetCategoryUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=AssetCategoryService.update(db, category_id, payload))


@router.delete("/{category_id}", status_code=204)
def delete_asset_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    AssetCategoryService.soft_delete(db, category_id)
