"""Posts CashTransaction events to the GL -- see app/posting_rules/__init__.py's
documented convention. Fires unconditionally on create (mirrors
posting_rules/cheque.py's `post_cheque_received`): a cash transaction is already a
real, immediate event the moment it's recorded, unlike Bill/Invoice's draft staging.

Only fires when `CashTransaction.contra_account_id` is set -- not every cash
transaction is wired to the GL yet, same partial-wiring pattern as everywhere else.

Uses the seeded "1020 Cash on hand - petty cash" asset account.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, CashTransaction, JournalEntry, JournalEntryLine
from app.posting_rules import new_entry

CASH_ON_HAND_CODE = "1020"


def _cash_account(db: Session) -> Account | None:
    return db.scalar(select(Account).where(Account.code == CASH_ON_HAND_CODE, Account.is_deleted.is_(False)))


def post_cash_transaction(db: Session, txn: CashTransaction) -> JournalEntry | None:
    """`in`: Dr cash on hand / Cr contra account. `out`: Dr contra account / Cr cash
    on hand."""
    if txn.contra_account_id is None:
        return None
    cash_account = _cash_account(db)
    if cash_account is None:
        return None

    entry = new_entry(db, txn.date, "cash_transaction", f"Cash {txn.direction} -- {txn.category or txn.reference or ''}".strip())
    if txn.direction == "in":
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=cash_account.id, debit=txn.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=txn.contra_account_id, debit=0, credit=txn.amount))
    else:
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=txn.contra_account_id, debit=txn.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=cash_account.id, debit=0, credit=txn.amount))
    db.flush()
    return entry
