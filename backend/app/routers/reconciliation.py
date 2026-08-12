import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.reconciliation import MatchSuggestionsOut
from app.services.reconciliation import ReconciliationService

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.get("/match-suggestions", response_model=MatchSuggestionsOut)
def match_suggestions(bank_account_id: uuid.UUID = Query(...), db: Session = Depends(get_db)):
    return ReconciliationService.suggest_matches(db, bank_account_id)
