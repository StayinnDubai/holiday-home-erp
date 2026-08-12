"""Posts Bill events to the GL -- see app/posting_rules/__init__.py's documented
convention. Direct mirror of cheque.py's shape, except Bill only posts once it
reaches 'recorded' (not unconditionally on create like Cheque, since a bill's
'draft' status explicitly isn't a confirmed liability yet -- a cheque is already a
real object at 'on_hand').

Only fires when the relevant FK is set: `Bill.contra_account_id` for the recorded
posting, `Bill.bank_account_id` (with that bank account's own `chart_account_id`)
for the paid posting -- neither is required, mirroring every other partial-GL-wiring
FK in this codebase (BankAccount.chart_account_id, Cheque.contra_account_id).

Uses the seeded "2010 Trade payables - suppliers" liability account as the holding
account for the unpaid balance between recording and payment.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, BankAccount, Bill, JournalEntry, JournalEntryLine
from app.posting_rules import new_entry

TRADE_PAYABLES_CODE = "2010"


def _payables_account(db: Session) -> Account | None:
    return db.scalar(select(Account).where(Account.code == TRADE_PAYABLES_CODE, Account.is_deleted.is_(False)))


def post_bill_recorded(db: Session, bill: Bill) -> JournalEntry | None:
    """Bill just reached 'recorded' -- Dr the chosen expense/cost account, Cr trade
    payables, for the bill amount (the confirmed, unpaid liability)."""
    if bill.contra_account_id is None:
        return None
    payables = _payables_account(db)
    if payables is None:
        return None

    entry = new_entry(db, bill.bill_date or date.today(), "bill", f"Bill {bill.bill_number} recorded")
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=bill.contra_account_id, debit=bill.amount, credit=0))
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=payables.id, debit=0, credit=bill.amount))
    db.flush()
    return entry


def post_bill_paid(db: Session, bill: Bill) -> JournalEntry | None:
    """Bill status just transitioned to 'paid' -- clears the payables liability
    against the bank account that paid it."""
    if bill.bank_account_id is None:
        return None
    bank_account = db.get(BankAccount, bill.bank_account_id)
    if bank_account is None or bank_account.chart_account_id is None:
        return None
    payables = _payables_account(db)
    if payables is None:
        return None

    entry = new_entry(db, date.today(), "bill", f"Bill {bill.bill_number} paid")
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=payables.id, debit=bill.amount, credit=0))
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=bank_account.chart_account_id, debit=0, credit=bill.amount))
    db.flush()
    return entry
