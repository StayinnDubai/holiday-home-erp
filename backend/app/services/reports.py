from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.schemas.reports import AccountBalanceLine, BalanceSheetOut, PnlOut, TrialBalanceOut


def _account_balances(
    db: Session, date_from: date | None, date_to: date, account_types: tuple[str, ...] | None = None
) -> list[AccountBalanceLine]:
    """Sums posted lines per account (doc §2.0's [D]/[F] flags don't affect this --
    Model B accounts simply never have posted lines in v1, JournalEntryService already
    refuses to post to them). Only `status == 'posted'` entries count, matching every
    other v1 scope decision in this pass (draft/submitted/approved are inert)."""
    stmt = (
        select(
            Account.id,
            Account.code,
            Account.name,
            Account.account_type,
            Account.normal_balance,
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .select_from(Account)
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
        .where(
            JournalEntry.status == "posted",
            JournalEntry.is_deleted.is_(False),
            JournalEntryLine.is_deleted.is_(False),
            JournalEntry.date <= date_to,
        )
        .group_by(Account.id)
        .order_by(Account.code)
    )
    if date_from is not None:
        stmt = stmt.where(JournalEntry.date >= date_from)
    if account_types:
        stmt = stmt.where(Account.account_type.in_(account_types))

    lines = []
    for account_id, code, name, account_type, normal_balance, debit, credit in db.execute(stmt).all():
        debit = float(debit)
        credit = float(credit)
        signed = (debit - credit) if normal_balance == "debit" else (credit - debit)
        lines.append(
            AccountBalanceLine(
                account_id=account_id,
                account_code=code,
                account_name=name,
                account_type=account_type,
                normal_balance=normal_balance,
                debit=round(debit, 2),
                credit=round(credit, 2),
                balance=round(signed, 2),
            )
        )
    return lines


class ReportsService:
    @staticmethod
    def trial_balance(db: Session, as_of: date) -> TrialBalanceOut:
        lines = _account_balances(db, None, as_of)
        return TrialBalanceOut(
            as_of=as_of.isoformat(),
            lines=lines,
            total_debit=round(sum(l.debit for l in lines), 2),
            total_credit=round(sum(l.credit for l in lines), 2),
        )

    @staticmethod
    def pnl(db: Session, date_from: date, date_to: date) -> PnlOut:
        revenue_lines = _account_balances(db, date_from, date_to, ("revenue",))
        cost_lines = _account_balances(db, date_from, date_to, ("cost",))
        total_revenue = round(sum(l.balance for l in revenue_lines), 2)
        total_cost = round(sum(l.balance for l in cost_lines), 2)
        return PnlOut(
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            revenue_lines=revenue_lines,
            cost_lines=cost_lines,
            total_revenue=total_revenue,
            total_cost=total_cost,
            net_income=round(total_revenue - total_cost, 2),
        )

    @staticmethod
    def balance_sheet(db: Session, as_of: date) -> BalanceSheetOut:
        asset_lines = _account_balances(db, None, as_of, ("asset",))
        liability_lines = _account_balances(db, None, as_of, ("liability",))
        equity_lines = _account_balances(db, None, as_of, ("equity",))
        pnl = ReportsService.pnl(db, date(as_of.year, 1, 1), as_of)
        return BalanceSheetOut(
            as_of=as_of.isoformat(),
            asset_lines=asset_lines,
            liability_lines=liability_lines,
            equity_lines=equity_lines,
            total_assets=round(sum(l.balance for l in asset_lines), 2),
            total_liabilities=round(sum(l.balance for l in liability_lines), 2),
            total_equity=round(sum(l.balance for l in equity_lines), 2),
            current_year_result=pnl.net_income,
        )
