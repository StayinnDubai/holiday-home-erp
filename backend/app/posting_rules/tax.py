"""Shared VAT-line helper for posting_rules/bill.py and posting_rules/invoice.py --
see app/posting_rules/__init__.py's documented convention.

Given a TaxCode's `treatment` and a `tax_amount`, returns the extra JournalEntryLine
row(s) a posting rule should add alongside its normal Dr/Cr pair:

- `standard`: one line on the Input VAT (1600, purchase side) or Output VAT (2400,
  sale side) account -- the caller is responsible for making its payable/receivable
  line gross (amount + tax_amount) instead of net.
- `zero` / `exempt`: no VAT line.
- `reverse_charge` (purchase/import side only, per UAE VAT -- Invoices treat this the
  same as zero/exempt): a self-accounted pair, Dr 1620 Input VAT - reverse charge /
  Cr 2410 Output VAT - reverse charge, both for tax_amount -- net zero cash impact,
  and the payable line stays net (no VAT added to what's owed the supplier).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import Account, JournalEntryLine
from app.models.foundation import TaxCode

INPUT_VAT_CODE = "1600"
INPUT_VAT_REVERSE_CHARGE_CODE = "1620"
OUTPUT_VAT_CODE = "2400"
OUTPUT_VAT_REVERSE_CHARGE_CODE = "2410"


def _account(db: Session, code: str) -> Account | None:
    return db.scalar(select(Account).where(Account.code == code, Account.is_deleted.is_(False)))


def vat_lines(db: Session, journal_entry_id, tax_code: TaxCode | None, tax_amount: float, side: str) -> list[JournalEntryLine]:
    """`side` is 'purchase' (Bill) or 'sale' (Invoice). Returns unsaved
    JournalEntryLine objects -- the caller adds them to the session alongside its
    own lines and flushes once."""
    if tax_code is None or not tax_amount:
        return []

    if tax_code.treatment == "standard":
        code = INPUT_VAT_CODE if side == "purchase" else OUTPUT_VAT_CODE
        account = _account(db, code)
        if account is None:
            return []
        # Purchase: Dr Input VAT (recoverable). Sale: Cr Output VAT (payable).
        if side == "purchase":
            return [JournalEntryLine(journal_entry_id=journal_entry_id, account_id=account.id, debit=tax_amount, credit=0)]
        return [JournalEntryLine(journal_entry_id=journal_entry_id, account_id=account.id, debit=0, credit=tax_amount)]

    if tax_code.treatment == "reverse_charge" and side == "purchase":
        input_rc = _account(db, INPUT_VAT_REVERSE_CHARGE_CODE)
        output_rc = _account(db, OUTPUT_VAT_REVERSE_CHARGE_CODE)
        if input_rc is None or output_rc is None:
            return []
        return [
            JournalEntryLine(journal_entry_id=journal_entry_id, account_id=input_rc.id, debit=tax_amount, credit=0),
            JournalEntryLine(journal_entry_id=journal_entry_id, account_id=output_rc.id, debit=0, credit=tax_amount),
        ]

    # zero | exempt | reverse_charge-on-a-sale (treated like zero/exempt)
    return []


def gross_amount(tax_code: TaxCode | None, amount: float, tax_amount: float) -> float:
    """The payable/receivable line's amount -- gross (amount + tax) for `standard`,
    net (amount only) for everything else, including reverse_charge (the VAT there
    nets to zero via the self-accounted pair, so it never touches what's owed)."""
    if tax_code is not None and tax_code.treatment == "standard":
        return amount + tax_amount
    return amount
