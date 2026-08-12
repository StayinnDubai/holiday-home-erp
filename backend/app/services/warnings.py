"""Warnings page (repurposes the reports/compliance-dashboard nav slot) -- aggregates
existing, already-computable concerns into one read-only list. No new "alert" concept
is invented here: every source below is data that already exists elsewhere in the
app but wasn't visible anywhere as a single unified view.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams
from app.models.accounting import Bill, Cheque, Invoice
from app.models.leasing import EjariRegistration, TenancyContract
from app.models.permits import DtcmPermit
from app.schemas.warnings import Warning, WarningsOut
from app.services.inventory import InventoryItemService
from app.services.leasing import EjariRegistrationService
from app.services.reports import ReportsService, OUTSTANDING_BILL_STATUSES

CONTRACT_EXPIRING_WINDOW_DAYS = 30
DTCM_EXPIRING_WINDOW_DAYS = 30
LOW_STOCK_THRESHOLD = 5
# Same statuses as OUTSTANDING_BILL_STATUSES (services/reports.py), plus 'part_paid'
# -- an outstanding-but-partially-settled invoice is still overdue if past due_date.
OUTSTANDING_INVOICE_STATUSES = OUTSTANDING_BILL_STATUSES + ("part_paid",)


class WarningsService:
    @staticmethod
    def get_warnings(db: Session) -> WarningsOut:
        today = date.today()
        items: list[Warning] = []

        items += WarningsService._overdue_bills(db, today)
        items += WarningsService._overdue_invoices(db, today)
        items += WarningsService._bounced_cheques(db)
        items += WarningsService._expiring_contracts(db, today)
        items += WarningsService._low_stock(db)
        items += WarningsService._ejari_variances(db)
        items += WarningsService._dtcm_permits_expiring(db, today)
        items += WarningsService._dtcm_operator_licenses_expiring(db, today)
        items += WarningsService._trial_balance_check(db, today)

        counts: dict[str, int] = {}
        for w in items:
            counts[w.category] = counts.get(w.category, 0) + 1

        return WarningsOut(items=items, counts=counts, total=len(items))

    @staticmethod
    def _overdue_bills(db: Session, today: date) -> list[Warning]:
        rows = db.execute(
            select(Bill).where(
                Bill.is_deleted.is_(False), Bill.status.in_(OUTSTANDING_BILL_STATUSES), Bill.due_date < today
            )
        ).scalars().all()
        return [
            Warning(
                category="overdue_bill",
                severity="warning",
                message=f"Bill {b.bill_number} was due {b.due_date.isoformat()} and is still {b.status}.",
                entity_type="bill",
                entity_id=b.id,
            )
            for b in rows
        ]

    @staticmethod
    def _overdue_invoices(db: Session, today: date) -> list[Warning]:
        rows = db.execute(
            select(Invoice).where(
                Invoice.is_deleted.is_(False), Invoice.status.in_(OUTSTANDING_INVOICE_STATUSES), Invoice.due_date < today
            )
        ).scalars().all()
        return [
            Warning(
                category="overdue_invoice",
                severity="warning",
                message=f"Invoice {i.invoice_number} was due {i.due_date.isoformat()} and is still {i.status}.",
                entity_type="invoice",
                entity_id=i.id,
            )
            for i in rows
        ]

    @staticmethod
    def _bounced_cheques(db: Session) -> list[Warning]:
        rows = db.execute(select(Cheque).where(Cheque.is_deleted.is_(False), Cheque.status == "bounced")).scalars().all()
        return [
            Warning(
                category="bounced_cheque",
                severity="critical",
                message=f"Cheque {c.cheque_number} ({c.direction}, {c.amount:.2f}) bounced.",
                entity_type="cheque",
                entity_id=c.id,
            )
            for c in rows
        ]

    @staticmethod
    def _expiring_contracts(db: Session, today: date) -> list[Warning]:
        cutoff = today + timedelta(days=CONTRACT_EXPIRING_WINDOW_DAYS)
        rows = db.execute(
            select(TenancyContract).where(
                TenancyContract.is_deleted.is_(False),
                TenancyContract.status == "active",
                TenancyContract.end_date < cutoff,
            )
        ).scalars().all()
        return [
            Warning(
                category="expiring_contract",
                severity="info",
                message=f"Tenancy contract {c.contract_number} expires {c.end_date.isoformat()}.",
                entity_type="tenancy_contract",
                entity_id=c.id,
            )
            for c in rows
        ]

    @staticmethod
    def _low_stock(db: Session) -> list[Warning]:
        rows, _ = InventoryItemService.list_page(db, PaginationParams(page=1, page_size=200))
        return [
            Warning(
                category="low_stock",
                severity="warning",
                message=f"{item.code} -- {item.name} has only {item.quantity_on_hand:g} on hand.",
                entity_type="inventory_item",
                entity_id=item.id,
            )
            for item in rows
            if item.quantity_on_hand <= LOW_STOCK_THRESHOLD
        ]

    @staticmethod
    def _ejari_variances(db: Session) -> list[Warning]:
        rows = db.execute(select(EjariRegistration).where(EjariRegistration.is_deleted.is_(False))).scalars().all()
        EjariRegistrationService._attach_relations(db, rows)
        items: list[Warning] = []
        for r in rows:
            for message in getattr(r, "variance_warnings", []):
                items.append(
                    Warning(
                        category="ejari_variance",
                        severity="info",
                        message=f"Ejari for {r.contract_number}: {message}.",
                        entity_type="ejari_registration",
                        entity_id=r.id,
                    )
                )
        return items

    @staticmethod
    def _dtcm_permits_expiring(db: Session, today: date) -> list[Warning]:
        cutoff = today + timedelta(days=DTCM_EXPIRING_WINDOW_DAYS)
        rows = db.execute(
            select(DtcmPermit).where(
                DtcmPermit.is_deleted.is_(False),
                DtcmPermit.status == "active",
                DtcmPermit.expiry_date.isnot(None),
                DtcmPermit.expiry_date < cutoff,
            )
        ).scalars().all()
        return [
            Warning(
                category="dtcm_permit_expiring",
                severity="warning",
                message=f"DTCM permit {p.permit_number} expires {p.expiry_date.isoformat()}.",
                entity_type="dtcm_permit",
                entity_id=p.id,
            )
            for p in rows
        ]

    @staticmethod
    def _dtcm_operator_licenses_expiring(db: Session, today: date) -> list[Warning]:
        cutoff = today + timedelta(days=DTCM_EXPIRING_WINDOW_DAYS)
        rows = db.execute(
            select(DtcmPermit).where(
                DtcmPermit.is_deleted.is_(False),
                DtcmPermit.status == "active",
                DtcmPermit.operator_license_expiry_date.isnot(None),
                DtcmPermit.operator_license_expiry_date < cutoff,
            )
        ).scalars().all()
        return [
            Warning(
                category="dtcm_operator_license_expiring",
                severity="warning",
                message=f"DTCM permit {p.permit_number}: operator licence expires {p.operator_license_expiry_date.isoformat()}.",
                entity_type="dtcm_permit",
                entity_id=p.id,
            )
            for p in rows
        ]

    @staticmethod
    def _trial_balance_check(db: Session, today: date) -> list[Warning]:
        # Should never actually fire given double-entry is enforced at write time
        # (JournalEntryService._validate_lines) -- cheap and honest to include anyway.
        tb = ReportsService.trial_balance(db, today)
        if round(tb.total_debit, 2) != round(tb.total_credit, 2):
            return [
                Warning(
                    category="trial_balance_out_of_balance",
                    severity="critical",
                    message=f"Trial balance is out of balance: debits {tb.total_debit:.2f} vs. credits {tb.total_credit:.2f}.",
                    entity_type="trial_balance",
                    entity_id=None,
                )
            ]
        return []
