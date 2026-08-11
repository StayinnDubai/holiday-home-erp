import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pagination import PaginationParams, pagination_params
from app.schemas.common import ItemResponse, ListMeta, ListResponse
from app.schemas.leasing import TenancyContractCreate, TenancyContractOut, TenancyContractUpdate
from app.services.leasing import TenancyContractService

router = APIRouter(prefix="/tenancy-contracts", tags=["tenancy-contracts"])


@router.get("", response_model=ListResponse[TenancyContractOut])
def list_tenancy_contracts(db: Session = Depends(get_db), params: PaginationParams = Depends(pagination_params)):
    rows, total = TenancyContractService.list_page(db, params)
    return ListResponse(data=rows, meta=ListMeta(page=params.page, page_size=params.page_size, total=total))


@router.get("/{contract_id}", response_model=ItemResponse[TenancyContractOut])
def get_tenancy_contract(contract_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractService.get(db, contract_id))


@router.post("", response_model=ItemResponse[TenancyContractOut], status_code=201)
def create_tenancy_contract(payload: TenancyContractCreate, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractService.create(db, payload))


@router.patch("/{contract_id}", response_model=ItemResponse[TenancyContractOut])
def update_tenancy_contract(contract_id: uuid.UUID, payload: TenancyContractUpdate, db: Session = Depends(get_db)):
    return ItemResponse(data=TenancyContractService.update(db, contract_id, payload))


@router.delete("/{contract_id}", status_code=204)
def delete_tenancy_contract(contract_id: uuid.UUID, db: Session = Depends(get_db)):
    TenancyContractService.soft_delete(db, contract_id)
