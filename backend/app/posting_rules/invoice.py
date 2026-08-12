"""Posts Invoice events to the GL -- see app/posting_rules/__init__.py's documented
convention. Direct mirror of bill.py's shape, reversed for the receivable side:
Invoice only posts once it reaches 'recorded' (a 'draft' invoice isn't a confirmed
receivable yet).

Only fires when the relevant FK is set: `Invoice.contra_account_id` for the recorded
posting, `Invoice.bank_account_id` (with that bank account's own `chart_account_id`)
for the paid posting -- neither is required, mirroring Bill's same partial-GL-wiring
pattern.

Uses the seeded "1100 Trade receivables - tenants" asset account as the holding
account for the outstanding balance between recording and payment.

VAT (doc §5.7): when `Invoice.tax_code_id` is set, `post_invoice_recorded` adds
posting_rules/tax.py's Output VAT line and grosses up the receivable line for
`standard`-treatment invoices. `reverse_charge` is a purchase/import-side mechanic
only (see tax.py) -- an invoice with that treatment posts no VAT line, same as
zero/exempt.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, BankAccount, Invoice, JournalEntry, JournalEntryLine
from app.models.foundation import TaxCode
from app.posting_rules import new_entry
from app.posting_rules.tax import gross_amount, vat_lines

TRADE_RECEIVABLES_CODE = "1100"


def _receivables_account(db: Session) -> Account | None:
    return db.scalar(select(Account).where(Account.code == TRADE_RECEIVABLES_CODE, Account.is_deleted.is_(False)))


def post_invoice_recorded(db: Session, invoice: Invoice) -> JournalEntry | None:
    """Invoice just reached 'recorded' -- Dr trade receivables (gross, including
    VAT), Cr the chosen revenue account (net), plus any Output VAT line."""
    if invoice.contra_account_id is None:
        return None
    receivables = _receivables_account(db)
    if receivables is None:
        return None

    tax_code = db.get(TaxCode, invoice.tax_code_id) if invoice.tax_code_id else None
    receivable_amount = gross_amount(tax_code, invoice.amount, invoice.tax_amount)

    entry = new_entry(db, invoice.invoice_date or date.today(), "invoice", f"Invoice {invoice.invoice_number} recorded")
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=receivables.id, debit=receivable_amount, credit=0))
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=invoice.contra_account_id, debit=0, credit=invoice.amount))
    for line in vat_lines(db, entry.id, tax_code, invoice.tax_amount, "sale"):
        db.add(line)
    db.flush()
    return entry


def post_invoice_paid(db: Session, invoice: Invoice) -> JournalEntry | None:
    """Invoice status just transitioned to 'paid' -- clears the receivable against
    the bank account that received payment."""
    if invoice.bank_account_id is None:
        return None
    bank_account = db.get(BankAccount, invoice.bank_account_id)
    if bank_account is None or bank_account.chart_account_id is None:
        return None
    receivables = _receivables_account(db)
    if receivables is None:
        return None

    tax_code = db.get(TaxCode, invoice.tax_code_id) if invoice.tax_code_id else None
    receivable_amount = gross_amount(tax_code, invoice.amount, invoice.tax_amount)

    entry = new_entry(db, date.today(), "invoice", f"Invoice {invoice.invoice_number} paid")
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=bank_account.chart_account_id, debit=receivable_amount, credit=0))
    db.add(JournalEntryLine(journal_entry_id=entry.id, account_id=receivables.id, debit=0, credit=receivable_amount))
    db.flush()
    return entry
