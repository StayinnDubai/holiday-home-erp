import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


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


# ---------- Bank account (Accounting > Bank Accounts) ----------
class BankAccountBase(BaseModel):
    code: str = Field(pattern=r"^\d{3}$")  # manually entered, exactly 3 digits, unique
    bank_id: uuid.UUID
    account_name: str
    account_type: str | None = None
    account_iban: str | None = None
    account_number: str | None = None
    # Optional here so the service can default it to the "AED" currency when
    # omitted (same effective default the old free-text column had).
    currency_id: uuid.UUID | None = None
    status: str = "active"  # active | closed | freezed
    open_date: date | None = None
    close_date: date | None = None
    chart_account_id: uuid.UUID | None = None


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    code: str | None = Field(default=None, pattern=r"^\d{3}$")
    bank_id: uuid.UUID | None = None
    account_name: str | None = None
    account_type: str | None = None
    account_iban: str | None = None
    account_number: str | None = None
    currency_id: uuid.UUID | None = None
    status: str | None = None
    open_date: date | None = None
    close_date: date | None = None
    chart_account_id: uuid.UUID | None = None


class BankAccountOut(BankAccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    currency_id: uuid.UUID
    bank_name: str | None = None
    chart_account_code: str | None = None
    currency_name: str | None = None


# ---------- Bank account columns (Settings > Bank Account Columns) ----------
# Drives both Bank Statement - Original and Bank Statement - Reconciliation,
# distinguished by `applies_to`.
class BankAccountColumnBase(BaseModel):
    bank_account_id: uuid.UUID
    applies_to: str = "reconciliation"  # original | reconciliation
    key: str
    label: str
    data_type: str = "text"  # text | number | date
    sort_order: int = 0


class BankAccountColumnCreate(BankAccountColumnBase):
    pass


class BankAccountColumnUpdate(BaseModel):
    bank_account_id: uuid.UUID | None = None
    applies_to: str | None = None
    key: str | None = None
    label: str | None = None
    data_type: str | None = None
    sort_order: int | None = None


class BankAccountColumnOut(BankAccountColumnBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bank_account_label: str | None = None


# ---------- Bank statement entries (Accounting > Bank Statement - Original / Reconciliation) ----------
class BankStatementEntryBase(BaseModel):
    bank_account_id: uuid.UUID
    kind: str = "reconciliation"  # original | reconciliation
    values: dict = Field(default_factory=dict)


class BankStatementEntryCreate(BankStatementEntryBase):
    pass


class BankStatementEntryUpdate(BaseModel):
    values: dict | None = None


class BankStatementEntryOut(BankStatementEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
