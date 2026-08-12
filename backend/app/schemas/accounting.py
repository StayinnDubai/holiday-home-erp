import uuid
from datetime import date as _date

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
    cheque_date: _date | None = None
    # doc: two ways to set this -- typed manually, or reconciled against a bank
    # statement. `drawdown_source` records which; requires actual_drawdown_date.
    actual_drawdown_date: _date | None = None
    drawdown_source: str | None = None  # manual | bank_reconciliation
    status: str = "on_hand"
    # The other side of this cheque's GL posting -- optional, drives posting_rules/cheque.py.
    contra_account_id: uuid.UUID | None = None
    # Which of the company's bank accounts this clears through once cleared -- optional,
    # also drives posting_rules/cheque.py.
    bank_account_id: uuid.UUID | None = None
    # Set once a reconciliation match is confirmed (services/reconciliation.py).
    matched_bank_statement_entry_id: uuid.UUID | None = None


class ChequeCreate(ChequeBase):
    pass


class ChequeUpdate(BaseModel):
    cheque_number: str | None = None
    direction: str | None = None
    counterparty_id: uuid.UUID | None = None
    payee_name: str | None = None
    amount: float | None = None
    cheque_date: _date | None = None
    actual_drawdown_date: _date | None = None
    drawdown_source: str | None = None
    status: str | None = None
    contra_account_id: uuid.UUID | None = None
    bank_account_id: uuid.UUID | None = None
    matched_bank_statement_entry_id: uuid.UUID | None = None


class ChequeOut(ChequeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    counterparty_name: str | None = None
    contra_account_code: str | None = None
    bank_account_label: str | None = None


# ---------- Bill (doc §6, accounts payable) ----------
class BillBase(BaseModel):
    supplier_counterparty_id: uuid.UUID
    unit_id: uuid.UUID | None = None
    bill_date: _date | None = None
    due_date: _date | None = None
    amount: float
    status: str = "draft"  # draft | recorded | scheduled | paid | disputed | cancelled
    # The expense/cost account this bill debits once recorded -- optional, drives
    # posting_rules/bill.py.
    contra_account_id: uuid.UUID | None = None
    # Which bank account pays this bill once 'paid' -- optional, also drives
    # posting_rules/bill.py.
    bank_account_id: uuid.UUID | None = None


class BillCreate(BillBase):
    pass


class BillUpdate(BaseModel):
    supplier_counterparty_id: uuid.UUID | None = None
    unit_id: uuid.UUID | None = None
    bill_date: _date | None = None
    due_date: _date | None = None
    amount: float | None = None
    status: str | None = None
    contra_account_id: uuid.UUID | None = None
    bank_account_id: uuid.UUID | None = None


class BillOut(BillBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bill_number: str
    supplier_name: str | None = None
    unit_code: str | None = None
    contra_account_code: str | None = None
    bank_account_label: str | None = None


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
    open_date: _date | None = None
    close_date: _date | None = None
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
    open_date: _date | None = None
    close_date: _date | None = None
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
    # None | amount | date | reference -- drives services/reconciliation.py's matching.
    semantic_role: str | None = None


class BankAccountColumnCreate(BankAccountColumnBase):
    pass


class BankAccountColumnUpdate(BaseModel):
    bank_account_id: uuid.UUID | None = None
    applies_to: str | None = None
    key: str | None = None
    label: str | None = None
    data_type: str | None = None
    sort_order: int | None = None
    semantic_role: str | None = None


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


# ---------- Journal entries (doc §3.5) -- lines travel with the header (like
# TenancyContract's landlord_ids) rather than as a separate sub-resource, since a
# balanced entry only makes sense as one atomic set of lines, not line-by-line edits. ----------
class JournalEntryLineIn(BaseModel):
    account_id: uuid.UUID
    unit_id: uuid.UUID | None = None
    debit: float = 0
    credit: float = 0
    description: str | None = None


class JournalEntryLineOut(JournalEntryLineIn):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_code: str | None = None
    account_name: str | None = None
    unit_code: str | None = None


class JournalEntryBase(BaseModel):
    date: _date
    status: str = "draft"  # draft | submitted | approved | posted | reversed
    source_module: str = "manual"
    memo: str | None = None


class JournalEntryCreate(JournalEntryBase):
    lines: list[JournalEntryLineIn] = Field(default_factory=list)


class JournalEntryUpdate(BaseModel):
    date: _date | None = None
    status: str | None = None
    memo: str | None = None
    lines: list[JournalEntryLineIn] | None = None


class JournalEntryOut(JournalEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    number: str
    period: str
    lines: list[JournalEntryLineOut] = Field(default_factory=list)
