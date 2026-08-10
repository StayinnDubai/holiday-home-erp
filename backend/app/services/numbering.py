from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.foundation import DocumentSequence


class NumberingService:
    """Configurable sequential numbering per document type (doc §5.4): prefix, year,
    reset-cycle. Call `.next(db, "unit")` etc. inside the same transaction as the
    record being numbered, so a rollback also rolls back the number (no gaps from
    abandoned attempts, which matters for tax-significant series like invoices).
    """

    @staticmethod
    def _advance(db: Session, doc_type: str) -> DocumentSequence:
        year = date.today().year
        seq = db.execute(
            select(DocumentSequence).where(
                DocumentSequence.doc_type == doc_type,
                DocumentSequence.year.is_(None),
            )
        ).scalar_one_or_none()

        if seq is None:
            seq = db.execute(
                select(DocumentSequence).where(
                    DocumentSequence.doc_type == doc_type,
                    DocumentSequence.year == year,
                )
            ).scalar_one_or_none()

        if seq is None:
            seq = DocumentSequence(doc_type=doc_type, prefix="", next_number=1, reset_cycle="never", year=None)
            db.add(seq)
            db.flush()

        seq.next_number += 1
        db.flush()
        return seq

    @staticmethod
    def raw_next(db: Session, doc_type: str) -> int:
        """Advances and returns the bare integer -- for callers with their own display
        format (e.g. unit_code's zero-padded-to-3-digits rule, doc §1.1), rather than
        this service's generic 6-digit formatting.
        """
        seq = NumberingService._advance(db, doc_type)
        return seq.next_number - 1

    @staticmethod
    def next(db: Session, doc_type: str) -> str:
        seq = NumberingService._advance(db, doc_type)
        number = seq.next_number - 1
        if seq.reset_cycle == "yearly":
            return f"{seq.prefix}{date.today().year}-{number:05d}"
        return f"{seq.prefix}{number:06d}"
