import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accounting import BankAccountColumn, BankStatementEntry, Cheque
from app.schemas.reconciliation import MatchSuggestion, MatchSuggestionsOut

# How many days apart a cheque's cheque_date and a bank statement entry's date can
# be and still be suggested as a match -- generous enough to cover typical
# clearing delays without matching unrelated transactions.
MATCH_DATE_WINDOW_DAYS = 10

OPEN_CHEQUE_STATUSES = ("on_hand", "deposited", "presented")


class ReconciliationService:
    """Suggests cheque <-> Bank Statement - Original matches for a bank account.
    Deliberately reuses ChequeService's existing update path to confirm a match
    (set status='cleared', actual_drawdown_date, drawdown_source='bank_reconciliation',
    matched_bank_statement_entry_id via a normal PATCH /cheques/{id}) rather than a
    separate confirm endpoint -- that's what makes the already-built
    posting_rules/cheque.py `post_cheque_cleared` fire automatically, no new
    posting logic needed here."""

    @staticmethod
    def suggest_matches(db: Session, bank_account_id: uuid.UUID) -> MatchSuggestionsOut:
        columns = db.scalars(
            select(BankAccountColumn).where(
                BankAccountColumn.bank_account_id == bank_account_id,
                BankAccountColumn.applies_to == "original",
                BankAccountColumn.is_deleted.is_(False),
            )
        ).all()
        amount_key = next((c.key for c in columns if c.semantic_role == "amount"), None)
        date_key = next((c.key for c in columns if c.semantic_role == "date"), None)
        if amount_key is None or date_key is None:
            # Honest "not configured yet" state -- no guessing which column means what.
            return MatchSuggestionsOut(bank_account_id=bank_account_id, configured=False)

        open_cheques = db.scalars(
            select(Cheque).where(
                Cheque.bank_account_id == bank_account_id,
                Cheque.status.in_(OPEN_CHEQUE_STATUSES),
                Cheque.matched_bank_statement_entry_id.is_(None),
                Cheque.is_deleted.is_(False),
            )
        ).all()
        if not open_cheques:
            return MatchSuggestionsOut(bank_account_id=bank_account_id, configured=True)

        already_matched_entry_ids = set(
            db.scalars(
                select(Cheque.matched_bank_statement_entry_id).where(
                    Cheque.bank_account_id == bank_account_id, Cheque.matched_bank_statement_entry_id.isnot(None)
                )
            ).all()
        )
        entries = db.scalars(
            select(BankStatementEntry).where(
                BankStatementEntry.bank_account_id == bank_account_id,
                BankStatementEntry.kind == "original",
                BankStatementEntry.is_deleted.is_(False),
            )
        ).all()

        candidates = []
        for entry in entries:
            if entry.id in already_matched_entry_ids:
                continue
            raw_amount = entry.values.get(amount_key)
            raw_date = entry.values.get(date_key)
            if raw_amount is None or raw_date is None:
                continue
            try:
                entry_amount = abs(float(raw_amount))
                entry_date = date.fromisoformat(str(raw_date)[:10])
            except (TypeError, ValueError):
                continue
            candidates.append({"entry": entry, "amount": entry_amount, "date": entry_date})

        suggestions: list[MatchSuggestion] = []
        used_entry_ids: set[uuid.UUID] = set()
        for cheque in open_cheques:
            if not cheque.cheque_date:
                continue
            best = None
            for candidate in candidates:
                if candidate["entry"].id in used_entry_ids:
                    continue
                if abs(candidate["amount"] - cheque.amount) > 0.01:
                    continue
                day_diff = abs((candidate["date"] - cheque.cheque_date).days)
                if day_diff > MATCH_DATE_WINDOW_DAYS:
                    continue
                if best is None or day_diff < best["day_diff"]:
                    best = {**candidate, "day_diff": day_diff}
            if best is not None:
                used_entry_ids.add(best["entry"].id)
                suggestions.append(
                    MatchSuggestion(
                        cheque_id=cheque.id,
                        cheque_number=cheque.cheque_number,
                        cheque_amount=cheque.amount,
                        cheque_date=cheque.cheque_date,
                        bank_statement_entry_id=best["entry"].id,
                        entry_amount=best["amount"],
                        entry_date=best["date"],
                        day_difference=best["day_diff"],
                    )
                )

        return MatchSuggestionsOut(bank_account_id=bank_account_id, configured=True, suggestions=suggestions)
