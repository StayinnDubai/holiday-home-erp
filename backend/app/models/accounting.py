"""Accounting-core tables. Only `Account` (the Chart of Accounts) is built in the
Foundation milestone -- it needs to exist so it can be seeded from Appendix A and
referenced by cost_type/setup_cost_type defaults later. Journal entries, cheques,
bills, etc. (plan §3.5) are built in the Accounting-core milestone.
"""
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base

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
