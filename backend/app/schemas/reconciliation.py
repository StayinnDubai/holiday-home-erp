import uuid
from datetime import date as _date

from pydantic import BaseModel, Field


class MatchSuggestion(BaseModel):
    cheque_id: uuid.UUID
    cheque_number: str
    cheque_amount: float
    cheque_date: _date | None
    bank_statement_entry_id: uuid.UUID
    entry_amount: float
    entry_date: _date
    day_difference: int


class MatchSuggestionsOut(BaseModel):
    bank_account_id: uuid.UUID
    # False if the account's Original columns haven't been tagged with an "amount"
    # and "date" semantic_role yet -- matching can't run without knowing which
    # JSONB key means what (see BankAccountColumn.semantic_role's doc comment).
    configured: bool
    suggestions: list[MatchSuggestion] = Field(default_factory=list)
