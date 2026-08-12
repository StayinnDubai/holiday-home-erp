"""Posts Cheque events to the GL -- see app/posting_rules/__init__.py's documented
convention (one `post_<event>(db, record) -> JournalEntry` per source event, called
by the owning service inside the same DB transaction as the operational write).

Only fires when the relevant FK is set: `Cheque.contra_account_id` for the initial
posting, `Cheque.bank_account_id` (with that bank account's own `chart_account_id`)
for the cleared posting. Neither is required on a Cheque -- not every cheque is wired
to the GL yet, mirroring BankAccount.chart_account_id's same partial-wiring pattern --
so an unset FK just means "no posting happens," not an error.

Models Appendix A's two-stage cheque lifecycle via the seeded holding accounts:
1030 "Cheques on hand - issued not presented" / 1040 "Cheques received - undeposited".
A cheque lands in its holding account when recorded, then moves into the actual bank
account once it clears -- exactly what those two account names describe.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, BankAccount, Cheque, JournalEntry, JournalEntryLine
from app.posting_rules import new_entry

CHEQUES_ISSUED_HOLDING_CODE = "1030"
CHEQUES_RECEIVED_HOLDING_CODE = "1040"


def _holding_account(db: Session, cheque: Cheque) -> Account | None:
    code = CHEQUES_RECEIVED_HOLDING_CODE if cheque.direction == "received" else CHEQUES_ISSUED_HOLDING_CODE
    return db.scalar(select(Account).where(Account.code == code, Account.is_deleted.is_(False)))


def post_cheque_received(db: Session, cheque: Cheque) -> JournalEntry | None:
    """Cheque just entered the ledger. Dr/Cr the holding account against the
    user-picked contra account (e.g. the receivable/payable it settles)."""
    if cheque.contra_account_id is None:
        return None
    holding_account = _holding_account(db, cheque)
    if holding_account is None:
        return None

    entry = new_entry(
        db, cheque.cheque_date or date.today(), "cheque", f"Cheque {cheque.cheque_number} ({cheque.direction})"
    )
    if cheque.direction == "received":
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=holding_account.id, debit=cheque.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=cheque.contra_account_id, debit=0, credit=cheque.amount))
    else:
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=cheque.contra_account_id, debit=cheque.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=holding_account.id, debit=0, credit=cheque.amount))
    db.flush()
    return entry


def post_cheque_cleared(db: Session, cheque: Cheque) -> JournalEntry | None:
    """Cheque status just transitioned to 'cleared' -- moves it out of the holding
    account and into the bank account it actually cleared through."""
    if cheque.bank_account_id is None:
        return None
    bank_account = db.get(BankAccount, cheque.bank_account_id)
    if bank_account is None or bank_account.chart_account_id is None:
        return None
    holding_account = _holding_account(db, cheque)
    if holding_account is None:
        return None

    entry = new_entry(db, date.today(), "cheque", f"Cheque {cheque.cheque_number} cleared")
    if cheque.direction == "received":
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=bank_account.chart_account_id, debit=cheque.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=holding_account.id, debit=0, credit=cheque.amount))
    else:
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=holding_account.id, debit=cheque.amount, credit=0))
        db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=bank_account.chart_account_id, debit=0, credit=cheque.amount))
    db.flush()
    return entry
