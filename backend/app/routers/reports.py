from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.reports import AgedPayablesOut, BalanceSheetOut, ChequePositionOut, PnlOut, TrialBalanceOut
from app.services.reports import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/trial-balance", response_model=TrialBalanceOut)
def trial_balance(as_of: date = Query(default_factory=date.today), db: Session = Depends(get_db)):
    return ReportsService.trial_balance(db, as_of)


@router.get("/pnl", response_model=PnlOut)
def pnl(
    date_from: date = Query(...),
    date_to: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    return ReportsService.pnl(db, date_from, date_to)


@router.get("/balance-sheet", response_model=BalanceSheetOut)
def balance_sheet(as_of: date = Query(default_factory=date.today), db: Session = Depends(get_db)):
    return ReportsService.balance_sheet(db, as_of)


@router.get("/aged-payables", response_model=AgedPayablesOut)
def aged_payables(as_of: date = Query(default_factory=date.today), db: Session = Depends(get_db)):
    return ReportsService.aged_payables(db, as_of)


@router.get("/cheque-position", response_model=ChequePositionOut)
def cheque_position(as_of: date = Query(default_factory=date.today), db: Session = Depends(get_db)):
    return ReportsService.cheque_position(db, as_of)
