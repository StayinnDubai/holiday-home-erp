"""Accounting-core tables. `Account` (the Chart of Accounts) was built in the
Foundation milestone -- it needs to exist so it can be seeded from Appendix A and
referenced by cost_type/setup_cost_type defaults later. `Cheque` (doc §2.1),
`Bill` (doc §6, accounts payable), and `BankStatementEntry` (doc §5.9 "bank
statements" import, feeds §2.10 reconciliation) are the operational sources that
post to the GL -- see app/posting_rules/ for the actual posting logic, one module
per source event.

Bank statement data (both "Original" and "Reconciliation") is column-per-bank-account
configurable (Settings > Bank Account Columns) rather than a fixed schema -- banks
export statements in different shapes, so `BankStatementEntry.values` is a JSONB blob
keyed by whatever columns that account's `BankAccountColumn` rows currently define,
for whichever of the two grids (`applies_to`/`kind`) is in play. `BankAccountColumn.
semantic_role` optionally tags which column means "amount"/"date"/"reference" for
that account, since `data_type` alone (text/number/date) can't disambiguate when an
account has several number- or date-typed columns (e.g. Debit vs Credit vs Balance)
-- reconciliation matching (services/reconciliation.py) needs to know which is which.
"""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base
from app.models.foundation import Currency
from app.models.master_data import Counterparty

# Doc Appendix A: account type buckets.
ACCOUNT_TYPES = ("asset", "liability", "equity", "revenue", "cost", "other")
NORMAL_BALANCES = ("debit", "credit")

# Only 'posted' entries count toward balances / Financial Reports (services/reports.py)
# -- draft/submitted/approved are visible but inert, matching standard GL practice.
JOURNAL_ENTRY_STATUSES = ("draft", "submitted", "approved", "posted", "reversed")


class Account(AuditableRecord, Base):
    """Chart of Accounts (doc §2.0 / Appendix A). `code` is the 4-digit account number
    from Appendix A (e.g. 5010 Rent - landlords). `requires_unit` mirrors the doc's
    non-negotiable rule that every [D] account cannot post without a unit dimension --
    enforced in the journal-posting service, not just documented here.
    """

    __tablename__ = "account"

    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(20))  # one of ACCOUNT_TYPES
    normal_balance: Mapped[str] = mapped_column(String(10))  # one of NORMAL_BALANCES
    control_account: Mapped[bool] = mapped_column(default=False)
    requires_unit: Mapped[bool] = mapped_column(default=False)  # Appendix A "[D]" flag
    is_model_b_only: Mapped[bool] = mapped_column(default=False)  # Appendix A "[F]" flag, unused in v1
    parent_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    active: Mapped[bool] = mapped_column(default=True)

    parent: Mapped["Account | None"] = relationship(remote_side="Account.id")


class Cheque(AuditableRecord, Base):
    """Cheque ledger (doc §2.1) -- post-dated cheques, both received (e.g. from a
    long-term tenant) and issued (e.g. to a landlord). `cheque_date` is the date
    written on the cheque; `actual_drawdown_date` is when it genuinely cleared the
    bank -- a materially different thing, so a distinct column rather than an
    overwrite of `cheque_date`.

    `actual_drawdown_date` can be set two ways, and `drawdown_source` records which:
    typed in directly ('manual'), or by reconciling against a bank statement
    ('bank_reconciliation'). Matching against actual imported bank statement lines is
    a later milestone -- for now this column only records *how* the date was set, so
    that matching can slot in later without a schema change.
    """

    __tablename__ = "cheque"

    cheque_number: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(10))  # received | issued
    counterparty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)
    payee_name: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    cheque_date: Mapped[date | None] = mapped_column(Date)

    actual_drawdown_date: Mapped[date | None] = mapped_column(Date)
    drawdown_source: Mapped[str | None] = mapped_column(String(20))  # manual | bank_reconciliation

    # on_hand|deposited|presented|cleared|bounced|replaced|returned|cancelled|held_as_security
    status: Mapped[str] = mapped_column(String(20), default="on_hand")

    # The other side of this cheque's GL posting (which receivable/payable/revenue
    # account it settles) -- optional, mirrors BankAccount.chart_account_id's same
    # "not every record is wired to the GL yet" pattern. Drives posting_rules/cheque.py.
    contra_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    # Which of the company's own bank accounts this cheque clears through once
    # `status` reaches 'cleared' -- needed so posting_rules/cheque.py knows which
    # bank account's chart_account_id to move the holding-account balance into.
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bank_account.id"))
    # Set once a reconciliation match is confirmed (services/reconciliation.py) --
    # records which imported bank statement line this cheque was matched against,
    # both for traceability and so the same entry doesn't get suggested again.
    matched_bank_statement_entry_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bank_statement_entry.id"))

    counterparty: Mapped[Counterparty] = relationship()
    contra_account: Mapped["Account | None"] = relationship()
    bank_account: Mapped["BankAccount | None"] = relationship()


class Bill(AuditableRecord, Base):
    """Accounts payable (doc §6). `status` moves draft -> recorded -> ... -> paid;
    reaching 'recorded' posts the liability (posting_rules/bill.py's
    `post_bill_recorded`, Dr `contra_account_id` / Cr "2010 Trade payables -
    suppliers"), reaching 'paid' clears it (`post_bill_paid`, Dr payables / Cr
    `bank_account_id`'s chart account) -- mirrors Cheque's two-stage posting, except
    Bill only posts once it reaches 'recorded' (unlike Cheque, which posts
    unconditionally on create -- a physical cheque is already a real event at
    'on_hand', whereas a bill's 'draft' status explicitly isn't a confirmed
    liability yet).
    """

    __tablename__ = "bill"

    bill_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    supplier_counterparty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("unit.id"))
    bill_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    # draft|recorded|scheduled|paid|disputed|cancelled
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Which expense/cost account this bill debits once recorded -- optional, mirrors
    # Cheque.contra_account_id. Drives posting_rules/bill.py.
    contra_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    # Which of the company's bank accounts pays this bill once 'paid' -- optional,
    # mirrors Cheque.bank_account_id.
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bank_account.id"))

    # VAT (doc §5.7) -- optional, drives posting_rules/tax.py's extra line(s) inside
    # post_bill_recorded. `tax_amount` is entered/computed client-side, not derived
    # here (matching every other numeric field in this codebase).
    tax_code_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tax_code.id"))
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), default=0)

    # Traceability only -- set when this bill was generated by
    # services/rent_schedule.py's rent auto-calculation, so the Bills grid can show
    # which tenancy contract it came from. Optional: manually-created bills leave
    # this null.
    tenancy_contract_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenancy_contract.id"))

    supplier: Mapped[Counterparty] = relationship()
    contra_account: Mapped["Account | None"] = relationship()
    bank_account: Mapped["BankAccount | None"] = relationship()


class Invoice(AuditableRecord, Base):
    """Accounts receivable -- the mirror of `Bill` for the revenue side. Reaching
    'recorded' posts Dr "1100 Trade receivables - tenants" (gross, including VAT)
    / Cr `contra_account_id` (net revenue) -- posting_rules/invoice.py's
    `post_invoice_recorded`; reaching 'paid' clears the receivable against
    `bank_account_id` (`post_invoice_paid`). Scoped AR-only (no `direction` field
    like the old plan sketch had) -- the purchase side is already Bill's job, and
    keeping both on one model would just create a confusing overlap.
    """

    __tablename__ = "invoice"

    invoice_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_counterparty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("unit.id"))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    # draft|recorded|scheduled|paid|disputed|part_paid|cancelled -- 'part_paid' is a
    # status label only, same as Bill: no partial-amount ledger exists in v1.
    status: Mapped[str] = mapped_column(String(20), default="draft")

    tax_code_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tax_code.id"))
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), default=0)

    # Which revenue account this invoice credits once recorded -- optional, mirrors
    # Bill.contra_account_id. Drives posting_rules/invoice.py.
    contra_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    # Which bank account receives payment once 'paid' -- optional, mirrors
    # Bill.bank_account_id.
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bank_account.id"))

    customer: Mapped[Counterparty] = relationship()
    contra_account: Mapped["Account | None"] = relationship()
    bank_account: Mapped["BankAccount | None"] = relationship()


class CashTransaction(AuditableRecord, Base):
    """Cash Ledger -- petty cash and cash collections by location/custodian (doc
    §2.2). Unlike Bill/Invoice, there's no draft/recorded staging here -- a cash
    transaction is already a real, immediate event the moment it's recorded (like a
    Cheque at 'on_hand'), so posting_rules/cash_transaction.py's `post_cash_
    transaction` fires unconditionally on create, moving "1020 Cash on hand - petty
    cash" against `contra_account_id` in the direction `direction` says.
    """

    __tablename__ = "cash_transaction"

    date: Mapped[date] = mapped_column(Date)
    direction: Mapped[str] = mapped_column(String(10))  # in | out
    # No user/auth model to FK to yet (plan §7) -- free text, matches the original
    # CASH_LEDGER_CONFIG scaffold.
    custodian_user_id: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    category: Mapped[str | None] = mapped_column(String(100))
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("counterparty.id"))
    reference: Mapped[str | None] = mapped_column(String(255))
    # The other side of this transaction's GL posting -- optional, mirrors every
    # other partial-GL-wiring FK in this codebase.
    contra_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))

    counterparty: Mapped["Counterparty | None"] = relationship()
    contra_account: Mapped["Account | None"] = relationship()


class BankAccount(AuditableRecord, Base):
    """Accounting > Bank Accounts -- the company's own bank accounts (distinct from
    `Counterparty`, which is the bank *as a counterparty* / signatory relationship
    the account sits under). `code` is a manually-entered 3-digit identifier, unique,
    never server-generated -- unlike e.g. `Unit.unit_code`, doc gave no numbering rule
    for this one."""

    __tablename__ = "bank_account"

    code: Mapped[str] = mapped_column(String(3), unique=True, index=True)
    bank_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str | None] = mapped_column(String(50))
    account_iban: Mapped[str | None] = mapped_column(String(50))
    account_number: Mapped[str | None] = mapped_column(String(50))
    currency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("currency.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | closed | freezed
    open_date: Mapped[date | None] = mapped_column(Date)
    close_date: Mapped[date | None] = mapped_column(Date)
    # The Chart of Accounts entry this bank account posts to (e.g. "1010 Bank -
    # current account") -- optional since not every bank account is wired to the GL yet.
    chart_account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))

    bank: Mapped[Counterparty] = relationship()
    chart_account: Mapped["Account | None"] = relationship()
    currency: Mapped[Currency] = relationship()


# Column data types offered by the Bank Account Columns designer (Settings).
BANK_ACCOUNT_COLUMN_TYPES = ("text", "number", "date")

# Optional tag saying what a column *means* for reconciliation matching
# (services/reconciliation.py) -- distinct from data_type, since an account can have
# several number/date columns (Debit, Credit, Balance; value date vs. posting date)
# with nothing else to say which one is "the" amount or date.
BANK_ACCOUNT_COLUMN_SEMANTIC_ROLES = ("amount", "date", "reference")

# Which grid a Bank Account Column / Bank Statement Entry belongs to -- the same
# designer (Settings > Bank Account Columns) and the same entry table now drive both
# Accounting > Bank Statement - Original and Bank Statement - Reconciliation, kept
# apart per bank account by this discriminator rather than two parallel schemas.
BANK_STATEMENT_VIEW_KINDS = ("original", "reconciliation")


class BankAccountColumn(AuditableRecord, Base):
    """Settings > Bank Account Columns -- each bank account defines its own column
    set for both "Bank Statement - Original" and "Bank Statement - Reconciliation"
    (banks export statements in different shapes, so there's no one fixed schema
    that fits all of them). `applies_to` says which of the two grids a column
    belongs to; `key` is the machine name used inside `BankStatementEntry.values`;
    `sort_order` controls column order within that grid."""

    __tablename__ = "bank_account_column"
    __table_args__ = (
        # Partial (not a plain UniqueConstraint) so a soft-deleted column's key
        # doesn't permanently block reusing that key on the same bank account --
        # only live (is_deleted = false) rows need to be distinct. Scoped by
        # applies_to too: "date" can exist once for Original and once for
        # Reconciliation on the same account without colliding.
        Index(
            "uq_bank_account_column_account_key",
            "bank_account_id",
            "applies_to",
            "key",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    bank_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bank_account.id"), nullable=False)
    applies_to: Mapped[str] = mapped_column(String(20), default="reconciliation")  # one of BANK_STATEMENT_VIEW_KINDS
    key: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))
    data_type: Mapped[str] = mapped_column(String(20), default="text")  # one of BANK_ACCOUNT_COLUMN_TYPES
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # One of BANK_ACCOUNT_COLUMN_SEMANTIC_ROLES, or None if this column isn't used
    # for reconciliation matching.
    semantic_role: Mapped[str | None] = mapped_column(String(20))

    bank_account: Mapped[BankAccount] = relationship()


class BankStatementEntry(AuditableRecord, Base):
    """Accounting > Bank Statement - Original / Reconciliation -- one row per bank
    account per entry, shaped entirely by that account's `BankAccountColumn` rows
    (Settings) rather than a fixed set of columns. `kind` says which of the two
    grids this row belongs to (mirrors `BankAccountColumn.applies_to`); `values` is
    keyed by that account+kind's configured column `key`s -- each grid renders
    whatever's currently configured for the selected account, reading/writing this
    blob rather than dedicated table columns."""

    __tablename__ = "bank_statement_entry"

    bank_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bank_account.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="reconciliation")  # one of BANK_STATEMENT_VIEW_KINDS
    values: Mapped[dict] = mapped_column(JSONB, default=dict)

    bank_account: Mapped[BankAccount] = relationship()


class JournalEntry(AuditableRecord, Base):
    """General ledger header (doc §3.5 `journal_entry`). Lines (`JournalEntryLine`)
    carry the actual debit/credit postings; this is just the envelope -- number,
    date, status, and which module produced it (`source_module`, e.g. 'manual' or
    'cheque' -- see app/posting_rules/). Only `status == 'posted'` entries count
    toward account balances / Financial Reports (services/reports.py); once posted,
    JournalEntryService blocks further edits to the entry's lines (mirrors
    leasing.py's LOCKED_FIELDS_WHEN_ACTIVE guard for active tenancy contracts) --
    corrections are a new reversing entry, not a history edit.
    """

    __tablename__ = "journal_entry"

    number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    date: Mapped[date] = mapped_column(Date)
    period: Mapped[str] = mapped_column(String(7))  # YYYY-MM, derived from date
    status: Mapped[str] = mapped_column(String(20), default="draft")  # one of JOURNAL_ENTRY_STATUSES
    source_module: Mapped[str] = mapped_column(String(30), default="manual")
    memo: Mapped[str | None] = mapped_column(String(500))


class JournalEntryLine(AuditableRecord, Base):
    """One debit or credit posting within a JournalEntry. Exactly one of debit/credit
    is non-zero per line (enforced in JournalEntryService) -- two columns rather than
    one signed amount, matching how a ledger is conventionally read. `unit_id` is the
    doc's "unit dimension" (Appendix A's [D] flag) -- required whenever
    `account.requires_unit` is true, enforced the same way as the doc's rule.
    """

    __tablename__ = "journal_entry_line"

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("journal_entry.id"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("unit.id"))
    debit: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), default=0)
    description: Mapped[str | None] = mapped_column(String(255))

    account: Mapped[Account] = relationship()
