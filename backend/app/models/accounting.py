"""Accounting-core tables. `Account` (the Chart of Accounts) was built in the
Foundation milestone -- it needs to exist so it can be seeded from Appendix A and
referenced by cost_type/setup_cost_type defaults later. `Cheque` (doc §2.1) and
`BankStatementEntry` (doc §5.9 "bank statements" import, feeds §2.10 reconciliation)
are the first slices of the Accounting-core milestone itself, built ahead of journal
entries/bills because their own columns were requested directly. Journal entries and
bills remain deferred -- neither a cheque nor a bank statement entry here posts to
the GL yet, and reconciliation is entered by hand rather than matched automatically.

Bank statement data (both "Original" and "Reconciliation") is column-per-bank-account
configurable (Settings > Bank Account Columns) rather than a fixed schema -- banks
export statements in different shapes, so `BankStatementEntry.values` is a JSONB blob
keyed by whatever columns that account's `BankAccountColumn` rows currently define,
for whichever of the two grids (`applies_to`/`kind`) is in play.
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

    counterparty: Mapped[Counterparty] = relationship()


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
