"""Lease daily calculation / ledger registration (backend/app/models/leasing.py's
`TenancyContract.auto_calculate_rent`). Fires once, from TenancyContractService, when
a contract transitions into (or is created directly as) `status='active'` with the
toggle on -- see that model's docstring for why this only ever runs once.

Generates a schedule of draft Bills against the landlord, one per
`instalment_count` period, reduced by any TenancyContractAdjustment rows (discount /
grace period / compensation, see that model). Bills are created 'draft' -- nothing
posts to the GL until a human reviews and records them (posting_rules/bill.py),
same as every manually-created Bill.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, Bill
from app.models.leasing import TenancyContract, TenancyContractAdjustment, TenancyContractParty
from app.services.numbering import NumberingService

RENT_EXPENSE_ACCOUNT_CODE = "5010"  # "Rent - landlords" (Appendix A)
DAYS_PER_YEAR = 365


def _daterange(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _rent_account(db: Session) -> Account | None:
    return db.scalar(select(Account).where(Account.code == RENT_EXPENSE_ACCOUNT_CODE, Account.is_deleted.is_(False)))


def _split_periods(start: date, end: date, count: int) -> list[tuple[date, date]]:
    """Splits [start, end] into `count` contiguous periods, as-even-as-possible by
    day count -- remainder days go to the earliest periods."""
    total_days = (end - start).days + 1
    count = max(1, count)
    base, remainder = divmod(total_days, count)
    periods: list[tuple[date, date]] = []
    cursor = start
    for i in range(count):
        period_days = base + (1 if i < remainder else 0)
        if period_days <= 0:
            continue
        period_end = cursor + timedelta(days=period_days - 1)
        periods.append((cursor, period_end))
        cursor = period_end + timedelta(days=1)
    return periods


def _day_amounts(contract: TenancyContract, adjustments: list[TenancyContractAdjustment]) -> dict[date, float]:
    daily_rate = contract.total_annual_rent / DAYS_PER_YEAR
    amounts = {d: daily_rate for d in _daterange(contract.start_date, contract.end_date)}

    for adj in adjustments:
        overlap = [d for d in _daterange(adj.start_date, adj.end_date) if d in amounts]
        if adj.type == "grace_period":
            for d in overlap:
                amounts[d] = 0.0
        elif adj.type == "discount" and adj.discount_pct:
            factor = 1 - (adj.discount_pct / 100)
            for d in overlap:
                amounts[d] = amounts[d] * factor

    return amounts


class RentScheduleService:
    @staticmethod
    def generate(db: Session, contract: TenancyContract) -> list[Bill]:
        rent_account = _rent_account(db)
        landlord_id = db.scalar(
            select(TenancyContractParty.landlord_id).where(TenancyContractParty.contract_id == contract.id).limit(1)
        )
        if rent_account is None or landlord_id is None:
            return []

        adjustments = list(
            db.scalars(
                select(TenancyContractAdjustment).where(
                    TenancyContractAdjustment.contract_id == contract.id, TenancyContractAdjustment.is_deleted.is_(False)
                )
            ).all()
        )
        compensations = [a for a in adjustments if a.type == "compensation" and a.amount]

        day_amounts = _day_amounts(contract, [a for a in adjustments if a.type != "compensation"])
        periods = _split_periods(contract.start_date, contract.end_date, contract.instalment_count)

        bills: list[Bill] = []
        for period_start, period_end in periods:
            period_total = sum(day_amounts.get(d, 0.0) for d in _daterange(period_start, period_end))
            for comp in compensations:
                if period_start <= comp.start_date <= period_end:
                    period_total -= comp.amount

            bill = Bill(
                bill_number=NumberingService.next(db, "bill"),
                supplier_counterparty_id=landlord_id,
                unit_id=contract.unit_id,
                bill_date=period_start,
                due_date=period_start,
                amount=round(period_total, 2),
                status="draft",
                contra_account_id=rent_account.id,
                tenancy_contract_id=contract.id,
            )
            db.add(bill)
            bills.append(bill)

        db.flush()
        contract.rent_schedule_generated = True
        return bills
