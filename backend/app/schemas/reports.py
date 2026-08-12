import uuid

from pydantic import BaseModel


# ---------- Financial Reports (read-only, computed from posted JournalEntryLine rows) ----------
class AccountBalanceLine(BaseModel):
    account_id: uuid.UUID
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    debit: float
    credit: float
    balance: float  # signed so its natural direction (per normal_balance) reads positive


class TrialBalanceOut(BaseModel):
    as_of: str
    lines: list[AccountBalanceLine]
    total_debit: float
    total_credit: float


class PnlOut(BaseModel):
    date_from: str
    date_to: str
    revenue_lines: list[AccountBalanceLine]
    cost_lines: list[AccountBalanceLine]
    total_revenue: float
    total_cost: float
    net_income: float


class BalanceSheetOut(BaseModel):
    as_of: str
    asset_lines: list[AccountBalanceLine]
    liability_lines: list[AccountBalanceLine]
    equity_lines: list[AccountBalanceLine]
    total_assets: float
    total_liabilities: float
    total_equity: float
    # Year-to-date P&L net income, computed on the fly and folded into equity so the
    # sheet actually balances -- v1 has no period-close step that would otherwise roll
    # this into the seeded "3040 Current year result" account for real.
    current_year_result: float


# ---------- Aged Payables (Bills have no partial-payment tracking, so "outstanding"
# is binary -- see services/reports.py's aged_payables docstring) ----------
class AgedPayableLine(BaseModel):
    bill_id: uuid.UUID
    bill_number: str
    supplier_name: str
    due_date: str | None
    amount: float
    bucket: str  # Current | 1-30 | 31-60 | 61-90 | 90+


class AgedPayablesOut(BaseModel):
    as_of: str
    lines: list[AgedPayableLine]
    bucket_totals: dict[str, float]
    grand_total: float


# ---------- Cheque Position (the `status` field already *is* the position) ----------
class ChequePositionGroup(BaseModel):
    direction: str  # received | issued
    status: str
    count: int
    total_amount: float


class ChequePositionOut(BaseModel):
    as_of: str
    groups: list[ChequePositionGroup]
