import uuid
from datetime import date
from datetime import date as _date  # bank statement line has a field literally named
# `date`, which shadows the `date` type inside its own class body -- alias avoids it.

from pydantic import BaseModel, ConfigDict


# ---------- Chart of accounts (doc §2.0 / Appendix A) ----------
class AccountBase(BaseModel):
    code: str
    name: str
    account_type: str  # asset | liability | equity | revenue | cost | other
    normal_balance: str  # debit | credit
    control_account: bool = False
    requires_unit: bool = False  # Appendix A "[D]"
    is_model_b_only: bool = False  # Appendix A "[F]"
    parent_account_id: uuid.UUID | None = None
    active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    account_type: str | None = None
    normal_balance: str | None = None
    control_account: bool | None = None
    requires_unit: bool | None = None
    is_model_b_only: bool | None = None
    parent_account_id: uuid.UUID | None = None
    active: bool | None = None


class AccountOut(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    parent_account_code: str | None = None


# ---------- Cheque ----------
class ChequeBase(BaseModel):
    cheque_number: str
    direction: str  # received | issued
    counterparty_id: uuid.UUID
    payee_name: str | None = None
    amount: float
    cheque_date: date | None = None
    # doc: two ways to set this -- typed manually, or reconciled against a bank
    # statement. `drawdown_source` records which; requires actual_drawdown_date.
    actual_drawdown_date: date | None = None
    drawdown_source: str | None = None  # manual | bank_reconciliation
    status: str = "on_hand"


class ChequeCreate(ChequeBase):
    pass


class ChequeUpdate(BaseModel):
    cheque_number: str | None = None
    direction: str | None = None
    counterparty_id: uuid.UUID | None = None
    payee_name: str | None = None
    amount: float | None = None
    cheque_date: date | None = None
    actual_drawdown_date: date | None = None
    drawdown_source: str | None = None
    status: str | None = None


class ChequeOut(ChequeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    counterparty_name: str | None = None


# ---------- Bank statement line ----------
class BankStatementLineBase(BaseModel):
    account_name: str
    account_type: str | None = None
    account_iban: str | None = None
    account_number: str | None = None
    card_number: str | None = None
    account_currency: str = "AED"

    transaction_type: str | None = None
    date: _date
    ref_number: str | None = None
    description: str | None = None
    amount: float
    balance: float | None = None
    original_ref_number: str | None = None
    notes: str | None = None


class BankStatementLineCreate(BankStatementLineBase):
    pass


class BankStatementLineUpdate(BaseModel):
    account_name: str | None = None
    account_type: str | None = None
    account_iban: str | None = None
    account_number: str | None = None
    card_number: str | None = None
    account_currency: str | None = None

    transaction_type: str | None = None
    date: _date | None = None
    ref_number: str | None = None
    description: str | None = None
    amount: float | None = None
    balance: float | None = None
    original_ref_number: str | None = None
    notes: str | None = None


class BankStatementLineOut(BankStatementLineBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
