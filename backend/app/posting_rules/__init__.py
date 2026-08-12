"""Maps operational events to journal entries.

Convention: one function per source event, named `post_<event>(db, <record>) -> JournalEntry`.
Each function is called by its owning service inside the same DB transaction as the
operational write it accounts for (see the plan's "Auto-posting" section).

`cheque.py`, `bill.py`, `invoice.py`, `cash_transaction.py` are populated, plus
`tax.py` (a shared VAT-line helper, not a `post_<event>` itself). Reservations don't
exist yet, so their posting rules stay deferred until that module is built.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.models.accounting import JournalEntry
from app.services.numbering import NumberingService


def new_entry(db: Session, entry_date: date, source_module: str, memo: str) -> JournalEntry:
    """Shared by every posting_rules/*.py module -- one JournalEntry header, always
    created 'posted' directly (these are all confirmed real-world events by the time
    a posting rule fires, unlike a manually-drafted entry)."""
    entry = JournalEntry(
        number=NumberingService.next(db, "journal_entry"),
        date=entry_date,
        period=entry_date.strftime("%Y-%m"),
        status="posted",
        source_module=source_module,
        memo=memo,
    )
    db.add(entry)
    db.flush()
    return entry
