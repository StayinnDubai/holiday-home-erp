"""Accounting-core tables. `Account` (the Chart of Accounts) was built in the
Foundation milestone -- it needs to exist so it can be seeded from Appendix A and
referenced by cost_type/setup_cost_type defaults later. `Cheque` (doc §2.1) and
`BankStatementLine` (doc §5.9 "bank statements" import, feeds §2.10 reconciliation)
are the first slices of the Accounting-core milestone itself, built ahead of journal
entries/bills because their own columns were requested directly. Journal entries and
bills remain deferred -- neither a cheque nor a bank statement line here posts to
the GL yet, and reconciliation is entered by hand rather than matched automatically.
"""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base
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


class BankStatementLine(AuditableRecord, Base):
    """Bank statement (doc §5.9: "CSV/Excel import ... for: ... bank statements" --
    entered one line at a time here for now rather than through that importer, which
    is still a separate later milestone). One row per transaction line as it appears
    on the statement, account identity columns included on every row rather than
    normalized into a separate bank-account table -- that mirrors how a bank's own
    CSV/Excel export is shaped, and is what a manual entry screen should match.

    Kept deliberately free of any matching/reconciliation logic against `Cheque` --
    doc §2.1's `drawdown_source='bank_reconciliation'` is set by hand against this
    data today; automatic matching is a later milestone once real import volume
    makes manual matching worth automating.
    """

    __tablename__ = "bank_statement_line"

    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str | None] = mapped_column(String(100))
    account_iban: Mapped[str | None] = mapped_column(String(50))
    account_number: Mapped[str | None] = mapped_column(String(50))
    card_number: Mapped[str | None] = mapped_column(String(50))
    account_currency: Mapped[str] = mapped_column(String(3), default="AED")

    transaction_type: Mapped[str | None] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date)
    ref_number: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    balance: Mapped[float | None] = mapped_column(Numeric(14, 2, asdecimal=False))
    original_ref_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
