import uuid

from sqlalchemy import Date, Numeric, cast, func, select
from sqlalchemy.orm import Session, aliased

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, apply_filters, paginate
from app.models.accounting import (
    Account,
    BankAccount,
    BankAccountColumn,
    BankStatementEntry,
    Bill,
    Cheque,
    JournalEntry,
    JournalEntryLine,
)
from app.models.foundation import Currency
from app.models.master_data import Counterparty, Unit
from app.posting_rules import bill as bill_posting
from app.posting_rules import cheque as cheque_posting
from app.schemas.accounting import (
    AccountCreate,
    AccountUpdate,
    BankAccountColumnCreate,
    BankAccountColumnUpdate,
    BankAccountCreate,
    BankAccountUpdate,
    BankStatementEntryCreate,
    BankStatementEntryUpdate,
    BillCreate,
    BillUpdate,
    ChequeCreate,
    ChequeUpdate,
    JournalEntryCreate,
    JournalEntryUpdate,
)
from app.services.audit import AuditService
from app.services.numbering import NumberingService

# Only 'posted' entries move a balance -- draft/submitted/approved are visible but inert.
JOURNAL_ENTRY_LOCKED_STATUSES = ("posted", "reversed")


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


def _default_currency_id(db: Session) -> uuid.UUID:
    """Resolves the "AED" currency for callers that don't pick one -- preserves the
    old free-text columns' default now that currency is a picked relation."""
    currency_id = db.scalar(select(Currency.id).where(Currency.name == "AED", Currency.is_deleted.is_(False)))
    if currency_id is None:
        raise ApiError(
            "No 'AED' currency is set up yet -- pick a currency explicitly or add one under Settings > Currencies.",
            code="invalid_reference",
            status_code=400,
        )
    return currency_id


def _validate_currency(db: Session, currency_id: uuid.UUID) -> None:
    currency = db.get(Currency, currency_id)
    if currency is None or currency.is_deleted:
        raise ApiError("Selected currency does not exist.", code="invalid_reference", status_code=400)


class AccountService:
    """Chart of Accounts (doc §2.0 / Appendix A). Seeded from app.seed.chart_of_accounts
    -- this service is the CRUD layer on top of that seed, e.g. for adding an account
    Appendix A didn't anticipate, or renaming one before it's used in a posting.
    """

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Account], int]:
        stmt = select(Account).where(Account.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Account.code.ilike(f"%{params.q}%") | Account.name.ilike(f"%{params.q}%"))
        needs_parent_join = params.sort_by == "parent_account_code" or "parent_account_code" in (params.filter_model or {})
        parent = aliased(Account)
        if needs_parent_join:
            stmt = stmt.outerjoin(parent, parent.id == Account.parent_account_id)
        stmt = apply_filters(
            stmt, Account, params.filter_model, extra_columns={"parent_account_code": parent.code} if needs_parent_join else None
        )
        if params.sort_by == "parent_account_code":
            col = parent.code
        else:
            col = _sort_col(Account, params.sort_by, Account.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        AccountService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, account_id: uuid.UUID) -> Account:
        row = db.get(Account, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Account not found.", code="not_found", status_code=404)
        AccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: AccountCreate) -> Account:
        AccountService._validate_unique_code(db, payload.code)
        if payload.parent_account_id is not None:
            AccountService._validate_parent(db, payload.parent_account_id)

        row = Account(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="account", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        AccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, account_id: uuid.UUID, payload: AccountUpdate) -> Account:
        row = db.get(Account, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Account not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            AccountService._validate_unique_code(db, data["code"])
        if data.get("parent_account_id") is not None:
            if data["parent_account_id"] == account_id:
                raise ApiError("An account cannot be its own parent.", code="invalid_reference", status_code=400)
            AccountService._validate_parent(db, data["parent_account_id"])

        for field, value in data.items():
            setattr(row, field, value)

        AuditService.log(db, entity_type="account", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        AccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, account_id: uuid.UUID) -> None:
        row = db.get(Account, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Account not found.", code="not_found", status_code=404)
        in_use = db.scalar(
            select(func.count()).select_from(Account).where(Account.parent_account_id == account_id, Account.is_deleted.is_(False))
        )
        if in_use:
            raise ApiError("Cannot delete an account that other accounts roll up to.", code="in_use", status_code=409)
        row.is_deleted = True
        AuditService.log(db, entity_type="account", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(Account.id).where(Account.code == code, Account.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Account code '{code}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _validate_parent(db: Session, parent_id: uuid.UUID) -> None:
        parent = db.get(Account, parent_id)
        if parent is None or parent.is_deleted:
            raise ApiError("Selected parent account does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_relations(db: Session, rows: list[Account]) -> None:
        if not rows:
            return
        parent_ids = [r.parent_account_id for r in rows if r.parent_account_id]
        parents: dict[uuid.UUID, str] = {}
        if parent_ids:
            parents = {a.id: a.code for a in db.scalars(select(Account).where(Account.id.in_(parent_ids))).all()}
        for r in rows:
            r.parent_account_code = parents.get(r.parent_account_id) if r.parent_account_id else None


class ChequeService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Cheque], int]:
        stmt = select(Cheque).where(Cheque.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Cheque.cheque_number.ilike(f"%{params.q}%"))
        needs_counterparty_join = params.sort_by == "counterparty_name" or "counterparty_name" in (params.filter_model or {})
        if needs_counterparty_join:
            stmt = stmt.join(Counterparty, Counterparty.id == Cheque.counterparty_id)
        stmt = apply_filters(
            stmt, Cheque, params.filter_model, extra_columns={"counterparty_name": Counterparty.name} if needs_counterparty_join else None
        )
        if params.sort_by == "counterparty_name":
            col = Counterparty.name
        else:
            col = _sort_col(Cheque, params.sort_by, Cheque.cheque_date)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        ChequeService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, cheque_id: uuid.UUID) -> Cheque:
        row = db.get(Cheque, cheque_id)
        if row is None or row.is_deleted:
            raise ApiError("Cheque not found.", code="not_found", status_code=404)
        ChequeService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: ChequeCreate) -> Cheque:
        ChequeService._validate_counterparty(db, payload.counterparty_id)
        ChequeService._validate_drawdown(payload.actual_drawdown_date, payload.drawdown_source)

        row = Cheque(**payload.model_dump())
        db.add(row)
        db.flush()
        # Same transaction as the operational write (posting_rules/__init__.py's
        # documented convention) -- a rollback here also rolls back the posting.
        cheque_posting.post_cheque_received(db, row)
        AuditService.log(db, entity_type="cheque", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        ChequeService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, cheque_id: uuid.UUID, payload: ChequeUpdate) -> Cheque:
        row = db.get(Cheque, cheque_id)
        if row is None or row.is_deleted:
            raise ApiError("Cheque not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "counterparty_id" in data:
            ChequeService._validate_counterparty(db, data["counterparty_id"])

        new_actual_drawdown_date = data.get("actual_drawdown_date", row.actual_drawdown_date)
        new_drawdown_source = data.get("drawdown_source", row.drawdown_source)
        # Clearing the date clears its source too -- they describe the same fact.
        if "actual_drawdown_date" in data and data["actual_drawdown_date"] is None and "drawdown_source" not in data:
            new_drawdown_source = None
            data["drawdown_source"] = None
        ChequeService._validate_drawdown(new_actual_drawdown_date, new_drawdown_source)

        old_status = row.status
        for field, value in data.items():
            setattr(row, field, value)

        if row.status == "cleared" and old_status != "cleared":
            cheque_posting.post_cheque_cleared(db, row)

        AuditService.log(db, entity_type="cheque", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        ChequeService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, cheque_id: uuid.UUID) -> None:
        row = db.get(Cheque, cheque_id)
        if row is None or row.is_deleted:
            raise ApiError("Cheque not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="cheque", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_counterparty(db: Session, counterparty_id: uuid.UUID) -> None:
        counterparty = db.get(Counterparty, counterparty_id)
        if counterparty is None or counterparty.is_deleted:
            raise ApiError("Selected counterparty does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_drawdown(actual_drawdown_date, drawdown_source) -> None:
        if drawdown_source and not actual_drawdown_date:
            raise ApiError(
                "drawdown_source can only be set alongside an actual drawdown date.",
                code="invalid_drawdown",
                status_code=400,
            )

    @staticmethod
    def _attach_relations(db: Session, rows: list[Cheque]) -> None:
        if not rows:
            return
        counterparty_ids = [r.counterparty_id for r in rows]
        counterparties = {
            c.id: c.name for c in db.scalars(select(Counterparty).where(Counterparty.id.in_(counterparty_ids))).all()
        }

        contra_account_ids = [r.contra_account_id for r in rows if r.contra_account_id]
        contra_accounts: dict[uuid.UUID, str] = {}
        if contra_account_ids:
            contra_accounts = {
                a.id: a.code for a in db.scalars(select(Account).where(Account.id.in_(contra_account_ids))).all()
            }

        bank_account_ids = [r.bank_account_id for r in rows if r.bank_account_id]
        bank_accounts: dict[uuid.UUID, str] = {}
        if bank_account_ids:
            bank_accounts = {
                a.id: a.account_name for a in db.scalars(select(BankAccount).where(BankAccount.id.in_(bank_account_ids))).all()
            }

        for r in rows:
            r.counterparty_name = counterparties.get(r.counterparty_id)
            r.contra_account_code = contra_accounts.get(r.contra_account_id) if r.contra_account_id else None
            r.bank_account_label = bank_accounts.get(r.bank_account_id) if r.bank_account_id else None


class BillService:
    """Accounts payable (doc §6). Direct mirror of ChequeService's shape -- status
    transitions into 'recorded'/'paid' trigger posting_rules/bill.py the same way
    ChequeService triggers posting_rules/cheque.py on create / transition into
    'cleared'."""

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[Bill], int]:
        stmt = select(Bill).where(Bill.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(Bill.bill_number.ilike(f"%{params.q}%"))
        needs_supplier_join = params.sort_by == "supplier_name" or "supplier_name" in (params.filter_model or {})
        if needs_supplier_join:
            stmt = stmt.join(Counterparty, Counterparty.id == Bill.supplier_counterparty_id)
        stmt = apply_filters(
            stmt, Bill, params.filter_model, extra_columns={"supplier_name": Counterparty.name} if needs_supplier_join else None
        )
        if params.sort_by == "supplier_name":
            col = Counterparty.name
        else:
            col = _sort_col(Bill, params.sort_by, Bill.bill_date)
        stmt = stmt.order_by(col.desc() if params.sort_dir != "asc" else col.asc())
        rows, total = paginate(db, stmt, params)
        BillService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, bill_id: uuid.UUID) -> Bill:
        row = db.get(Bill, bill_id)
        if row is None or row.is_deleted:
            raise ApiError("Bill not found.", code="not_found", status_code=404)
        BillService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BillCreate) -> Bill:
        BillService._validate_supplier(db, payload.supplier_counterparty_id)

        row = Bill(bill_number=NumberingService.next(db, "bill"), **payload.model_dump())
        db.add(row)
        db.flush()
        if row.status == "recorded":
            bill_posting.post_bill_recorded(db, row)
        AuditService.log(db, entity_type="bill", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        BillService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, bill_id: uuid.UUID, payload: BillUpdate) -> Bill:
        row = db.get(Bill, bill_id)
        if row is None or row.is_deleted:
            raise ApiError("Bill not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "supplier_counterparty_id" in data:
            BillService._validate_supplier(db, data["supplier_counterparty_id"])

        old_status = row.status
        for field, value in data.items():
            setattr(row, field, value)

        if row.status == "recorded" and old_status != "recorded":
            bill_posting.post_bill_recorded(db, row)
        if row.status == "paid" and old_status != "paid":
            bill_posting.post_bill_paid(db, row)

        AuditService.log(db, entity_type="bill", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        BillService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, bill_id: uuid.UUID) -> None:
        row = db.get(Bill, bill_id)
        if row is None or row.is_deleted:
            raise ApiError("Bill not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="bill", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_supplier(db: Session, counterparty_id: uuid.UUID) -> None:
        supplier = db.get(Counterparty, counterparty_id)
        if supplier is None or supplier.is_deleted:
            raise ApiError("Selected supplier does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_relations(db: Session, rows: list[Bill]) -> None:
        if not rows:
            return
        supplier_ids = [r.supplier_counterparty_id for r in rows]
        suppliers = {
            c.id: c.name for c in db.scalars(select(Counterparty).where(Counterparty.id.in_(supplier_ids))).all()
        }

        unit_ids = [r.unit_id for r in rows if r.unit_id]
        units: dict[uuid.UUID, str] = {}
        if unit_ids:
            units = {u.id: u.unit_code for u in db.scalars(select(Unit).where(Unit.id.in_(unit_ids))).all()}

        contra_account_ids = [r.contra_account_id for r in rows if r.contra_account_id]
        contra_accounts: dict[uuid.UUID, str] = {}
        if contra_account_ids:
            contra_accounts = {
                a.id: a.code for a in db.scalars(select(Account).where(Account.id.in_(contra_account_ids))).all()
            }

        bank_account_ids = [r.bank_account_id for r in rows if r.bank_account_id]
        bank_accounts: dict[uuid.UUID, str] = {}
        if bank_account_ids:
            bank_accounts = {
                a.id: a.account_name for a in db.scalars(select(BankAccount).where(BankAccount.id.in_(bank_account_ids))).all()
            }

        for r in rows:
            r.supplier_name = suppliers.get(r.supplier_counterparty_id)
            r.unit_code = units.get(r.unit_id) if r.unit_id else None
            r.contra_account_code = contra_accounts.get(r.contra_account_id) if r.contra_account_id else None
            r.bank_account_label = bank_accounts.get(r.bank_account_id) if r.bank_account_id else None


class BankAccountService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BankAccount], int]:
        stmt = select(BankAccount).where(BankAccount.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(BankAccount.code.ilike(f"%{params.q}%") | BankAccount.account_name.ilike(f"%{params.q}%"))
        filter_keys = (params.filter_model or {}).keys()
        needs_bank_join = params.sort_by == "bank_name" or "bank_name" in filter_keys
        needs_chart_join = params.sort_by == "chart_account_code" or "chart_account_code" in filter_keys
        needs_currency_join = params.sort_by == "currency_name" or "currency_name" in filter_keys
        if needs_bank_join:
            stmt = stmt.join(Counterparty, Counterparty.id == BankAccount.bank_id)
        if needs_chart_join:
            stmt = stmt.outerjoin(Account, Account.id == BankAccount.chart_account_id)
        if needs_currency_join:
            stmt = stmt.join(Currency, Currency.id == BankAccount.currency_id)
        extra_columns = {}
        if needs_bank_join:
            extra_columns["bank_name"] = Counterparty.name
        if needs_chart_join:
            extra_columns["chart_account_code"] = Account.code
        if needs_currency_join:
            extra_columns["currency_name"] = Currency.name
        stmt = apply_filters(stmt, BankAccount, params.filter_model, extra_columns=extra_columns or None)
        if params.sort_by == "bank_name":
            col = Counterparty.name
        elif params.sort_by == "chart_account_code":
            col = Account.code
        elif params.sort_by == "currency_name":
            col = Currency.name
        else:
            col = _sort_col(BankAccount, params.sort_by, BankAccount.code)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        BankAccountService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, account_id: uuid.UUID) -> BankAccount:
        row = db.get(BankAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account not found.", code="not_found", status_code=404)
        BankAccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BankAccountCreate) -> BankAccount:
        BankAccountService._validate_unique_code(db, payload.code)
        BankAccountService._validate_bank(db, payload.bank_id)
        if payload.chart_account_id is not None:
            BankAccountService._validate_chart_account(db, payload.chart_account_id)

        data = payload.model_dump()
        if data["currency_id"] is None:
            data["currency_id"] = _default_currency_id(db)
        else:
            _validate_currency(db, data["currency_id"])

        row = BankAccount(**data)
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="bank_account", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        BankAccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, account_id: uuid.UUID, payload: BankAccountUpdate) -> BankAccount:
        row = db.get(BankAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account not found.", code="not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] != row.code:
            BankAccountService._validate_unique_code(db, data["code"])
        if "bank_id" in data:
            BankAccountService._validate_bank(db, data["bank_id"])
        if data.get("chart_account_id") is not None:
            BankAccountService._validate_chart_account(db, data["chart_account_id"])
        if data.get("currency_id") is not None:
            _validate_currency(db, data["currency_id"])

        for field, value in data.items():
            setattr(row, field, value)

        AuditService.log(db, entity_type="bank_account", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        BankAccountService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, account_id: uuid.UUID) -> None:
        row = db.get(BankAccount, account_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="bank_account", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_unique_code(db: Session, code: str) -> None:
        existing = db.scalar(select(BankAccount.id).where(BankAccount.code == code, BankAccount.is_deleted.is_(False)))
        if existing:
            raise ApiError(f"Bank account code '{code}' is already in use.", code="duplicate_code", status_code=409)

    @staticmethod
    def _validate_bank(db: Session, bank_id: uuid.UUID) -> None:
        bank = db.get(Counterparty, bank_id)
        if bank is None or bank.is_deleted:
            raise ApiError("Selected bank does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_chart_account(db: Session, chart_account_id: uuid.UUID) -> None:
        account = db.get(Account, chart_account_id)
        if account is None or account.is_deleted:
            raise ApiError("Selected chart of account does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _attach_relations(db: Session, rows: list[BankAccount]) -> None:
        if not rows:
            return
        bank_ids = [r.bank_id for r in rows]
        banks = {c.id: c.name for c in db.scalars(select(Counterparty).where(Counterparty.id.in_(bank_ids))).all()}

        chart_account_ids = [r.chart_account_id for r in rows if r.chart_account_id]
        chart_accounts: dict[uuid.UUID, str] = {}
        if chart_account_ids:
            chart_accounts = {
                a.id: a.code for a in db.scalars(select(Account).where(Account.id.in_(chart_account_ids))).all()
            }

        currency_ids = [r.currency_id for r in rows]
        currencies = {c.id: c.name for c in db.scalars(select(Currency).where(Currency.id.in_(currency_ids))).all()}

        for r in rows:
            r.bank_name = banks.get(r.bank_id)
            r.chart_account_code = chart_accounts.get(r.chart_account_id) if r.chart_account_id else None
            r.currency_name = currencies.get(r.currency_id)


class BankAccountColumnService:
    """Settings > Bank Account Columns -- the designer behind both Accounting >
    Bank Statement - Original and Bank Statement - Reconciliation. Each bank
    account gets its own column set per view (banks export statements in
    different shapes), so every list here can be scoped to one `bank_account_id`
    and/or one `applies_to`."""

    @staticmethod
    def list_page(
        db: Session,
        params: PaginationParams,
        bank_account_id: uuid.UUID | None = None,
        applies_to: str | None = None,
    ) -> tuple[list[BankAccountColumn], int]:
        stmt = select(BankAccountColumn).where(BankAccountColumn.is_deleted.is_(False))
        if bank_account_id is not None:
            stmt = stmt.where(BankAccountColumn.bank_account_id == bank_account_id)
        if applies_to is not None:
            stmt = stmt.where(BankAccountColumn.applies_to == applies_to)
        if params.q:
            stmt = stmt.where(BankAccountColumn.label.ilike(f"%{params.q}%"))
        needs_account_join = params.sort_by == "bank_account_label" or "bank_account_label" in (params.filter_model or {})
        if needs_account_join:
            stmt = stmt.join(BankAccount, BankAccount.id == BankAccountColumn.bank_account_id)
        stmt = apply_filters(
            stmt,
            BankAccountColumn,
            params.filter_model,
            extra_columns={"bank_account_label": BankAccount.account_name} if needs_account_join else None,
        )
        if params.sort_by == "bank_account_label":
            col = BankAccount.account_name
        else:
            col = _sort_col(BankAccountColumn, params.sort_by, BankAccountColumn.sort_order)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        rows, total = paginate(db, stmt, params)
        BankAccountColumnService._attach_relations(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, column_id: uuid.UUID) -> BankAccountColumn:
        row = db.get(BankAccountColumn, column_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account column not found.", code="not_found", status_code=404)
        BankAccountColumnService._attach_relations(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: BankAccountColumnCreate) -> BankAccountColumn:
        BankAccountColumnService._validate_bank_account(db, payload.bank_account_id)
        BankAccountColumnService._validate_unique_key(db, payload.bank_account_id, payload.applies_to, payload.key)
        row = BankAccountColumn(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="bank_account_column", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        BankAccountColumnService._attach_relations(db, [row])
        return row

    @staticmethod
    def update(db: Session, column_id: uuid.UUID, payload: BankAccountColumnUpdate) -> BankAccountColumn:
        row = db.get(BankAccountColumn, column_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account column not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        if "bank_account_id" in data:
            BankAccountColumnService._validate_bank_account(db, data["bank_account_id"])
        if ("key" in data and data["key"] != row.key) or ("applies_to" in data and data["applies_to"] != row.applies_to):
            BankAccountColumnService._validate_unique_key(
                db,
                data.get("bank_account_id", row.bank_account_id),
                data.get("applies_to", row.applies_to),
                data.get("key", row.key),
                exclude_id=row.id,
            )
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="bank_account_column", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        BankAccountColumnService._attach_relations(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, column_id: uuid.UUID) -> None:
        row = db.get(BankAccountColumn, column_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank account column not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="bank_account_column", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_bank_account(db: Session, bank_account_id: uuid.UUID) -> None:
        account = db.get(BankAccount, bank_account_id)
        if account is None or account.is_deleted:
            raise ApiError("Selected bank account does not exist.", code="invalid_reference", status_code=400)

    @staticmethod
    def _validate_unique_key(
        db: Session, bank_account_id: uuid.UUID, applies_to: str, key: str, exclude_id: uuid.UUID | None = None
    ) -> None:
        stmt = select(BankAccountColumn.id).where(
            BankAccountColumn.bank_account_id == bank_account_id,
            BankAccountColumn.applies_to == applies_to,
            BankAccountColumn.key == key,
            BankAccountColumn.is_deleted.is_(False),
        )
        if exclude_id is not None:
            stmt = stmt.where(BankAccountColumn.id != exclude_id)
        if db.scalar(stmt):
            raise ApiError(
                f"Column key '{key}' is already used by another column on this bank account/view.",
                code="duplicate_code",
                status_code=409,
            )

    @staticmethod
    def _attach_relations(db: Session, rows: list[BankAccountColumn]) -> None:
        if not rows:
            return
        bank_account_ids = [r.bank_account_id for r in rows]
        accounts = {
            a.id: a.account_name for a in db.scalars(select(BankAccount).where(BankAccount.id.in_(bank_account_ids))).all()
        }
        for r in rows:
            r.bank_account_label = accounts.get(r.bank_account_id)


class BankStatementEntryService:
    """Accounting > Bank Statement - Original / Reconciliation -- one row per bank
    account per entry, its shape defined entirely by that account's
    `BankAccountColumn` rows (Settings > Bank Account Columns) rather than a fixed
    schema. `kind` scopes both which grid a list belongs to and, together with
    `bank_account_id`, which columns apply."""

    @staticmethod
    def list_page(
        db: Session,
        params: PaginationParams,
        bank_account_id: uuid.UUID | None = None,
        kind: str | None = None,
    ) -> tuple[list[BankStatementEntry], int]:
        stmt = select(BankStatementEntry).where(BankStatementEntry.is_deleted.is_(False))
        if bank_account_id is not None:
            stmt = stmt.where(BankStatementEntry.bank_account_id == bank_account_id)
        if kind is not None:
            stmt = stmt.where(BankStatementEntry.kind == kind)
        extra_columns = BankStatementEntryService._jsonb_filter_columns(
            db, bank_account_id, kind, (params.filter_model or {}).keys()
        )
        stmt = apply_filters(stmt, BankStatementEntry, params.filter_model, extra_columns=extra_columns)
        if params.sort_by and params.sort_by in extra_columns:
            col = extra_columns[params.sort_by]
        else:
            col = _sort_col(BankStatementEntry, params.sort_by, BankStatementEntry.created_at)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def _jsonb_filter_columns(db: Session, bank_account_id, kind, filter_keys):
        """`BankStatementEntry.values` is a JSONB blob (module docstring) -- ag-Grid's
        filterModel keys are the dynamic column `key`s defined in Settings > Bank
        Account Columns, not real model attributes, so `apply_filters`'s plain
        `getattr` fallback can't resolve them. Builds one JSONB-path expression per
        filtered key instead, cast to that column's configured `data_type` (text/
        number/date) so numeric/date filter operators (`greaterThan`, `inRange`, ...)
        compare correctly rather than as strings.
        """
        filter_keys = set(filter_keys)
        if not filter_keys:
            return {}
        data_types: dict[str, str] = {}
        if bank_account_id is not None and kind is not None:
            data_types = dict(
                db.execute(
                    select(BankAccountColumn.key, BankAccountColumn.data_type).where(
                        BankAccountColumn.bank_account_id == bank_account_id,
                        BankAccountColumn.applies_to == kind,
                        BankAccountColumn.is_deleted.is_(False),
                    )
                ).all()
            )
        extra_columns = {}
        for key in filter_keys:
            text_expr = BankStatementEntry.values[key].astext
            data_type = data_types.get(key, "text")
            if data_type == "number":
                extra_columns[key] = cast(text_expr, Numeric)
            elif data_type == "date":
                extra_columns[key] = cast(text_expr, Date)
            else:
                extra_columns[key] = text_expr
        return extra_columns

    @staticmethod
    def get(db: Session, entry_id: uuid.UUID) -> BankStatementEntry:
        row = db.get(BankStatementEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement entry not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: BankStatementEntryCreate) -> BankStatementEntry:
        BankStatementEntryService._validate_bank_account(db, payload.bank_account_id)
        row = BankStatementEntry(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="bank_statement_entry", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, entry_id: uuid.UUID, payload: BankStatementEntryUpdate) -> BankStatementEntry:
        row = db.get(BankStatementEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement entry not found.", code="not_found", status_code=404)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="bank_statement_entry", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, entry_id: uuid.UUID) -> None:
        row = db.get(BankStatementEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement entry not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="bank_statement_entry", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_bank_account(db: Session, bank_account_id: uuid.UUID) -> None:
        account = db.get(BankAccount, bank_account_id)
        if account is None or account.is_deleted:
            raise ApiError("Selected bank account does not exist.", code="invalid_reference", status_code=400)


class JournalEntryService:
    """General ledger (doc §3.5 `journal_entry`). Only `status == 'posted'` entries
    move a balance (services/reports.py) -- draft/submitted/approved are visible but
    inert. Once posted, an entry's lines are immutable (mirrors leasing.py's
    LOCKED_FIELDS_WHEN_ACTIVE guard for active tenancy contracts) -- corrections are
    a new reversing entry, not a history edit.
    """

    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[JournalEntry], int]:
        stmt = select(JournalEntry).where(JournalEntry.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(JournalEntry.number.ilike(f"%{params.q}%"))
        stmt = apply_filters(stmt, JournalEntry, params.filter_model)
        col = _sort_col(JournalEntry, params.sort_by, JournalEntry.date)
        stmt = stmt.order_by(col.desc() if params.sort_dir != "asc" else col.asc())
        rows, total = paginate(db, stmt, params)
        JournalEntryService._attach_lines(db, rows)
        return rows, total

    @staticmethod
    def get(db: Session, entry_id: uuid.UUID) -> JournalEntry:
        row = db.get(JournalEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Journal entry not found.", code="not_found", status_code=404)
        JournalEntryService._attach_lines(db, [row])
        return row

    @staticmethod
    def create(db: Session, payload: JournalEntryCreate) -> JournalEntry:
        JournalEntryService._validate_lines(db, payload.lines)
        data = payload.model_dump(exclude={"lines"})
        row = JournalEntry(number=NumberingService.next(db, "journal_entry"), period=data["date"].strftime("%Y-%m"), **data)
        db.add(row)
        db.flush()
        for line in payload.lines:
            db.add(JournalEntryLine(journal_entry_id=row.id, **line.model_dump()))
        AuditService.log(db, entity_type="journal_entry", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        JournalEntryService._attach_lines(db, [row])
        return row

    @staticmethod
    def update(db: Session, entry_id: uuid.UUID, payload: JournalEntryUpdate) -> JournalEntry:
        row = db.get(JournalEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Journal entry not found.", code="not_found", status_code=404)
        if row.status in JOURNAL_ENTRY_LOCKED_STATUSES:
            raise ApiError(
                "This entry is posted -- it's immutable. Create a reversing entry instead.",
                code="entry_locked",
                status_code=409,
            )

        data = payload.model_dump(exclude_unset=True, exclude={"lines"})
        if "date" in data:
            data["period"] = data["date"].strftime("%Y-%m")
        for field, value in data.items():
            setattr(row, field, value)

        if payload.lines is not None:
            JournalEntryService._validate_lines(db, payload.lines)
            db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == entry_id).delete()
            for line in payload.lines:
                db.add(JournalEntryLine(journal_entry_id=row.id, **line.model_dump()))

        AuditService.log(db, entity_type="journal_entry", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        JournalEntryService._attach_lines(db, [row])
        return row

    @staticmethod
    def soft_delete(db: Session, entry_id: uuid.UUID) -> None:
        row = db.get(JournalEntry, entry_id)
        if row is None or row.is_deleted:
            raise ApiError("Journal entry not found.", code="not_found", status_code=404)
        if row.status in JOURNAL_ENTRY_LOCKED_STATUSES:
            raise ApiError(
                "This entry is posted -- it's immutable. Create a reversing entry instead.",
                code="entry_locked",
                status_code=409,
            )
        row.is_deleted = True
        AuditService.log(db, entity_type="journal_entry", entity_id=row.id, action="delete")
        db.commit()

    @staticmethod
    def _validate_lines(db: Session, lines: list) -> None:
        if not lines:
            raise ApiError("A journal entry needs at least one line.", code="lines_required", status_code=400)

        account_ids = {line.account_id for line in lines}
        accounts = {a.id: a for a in db.scalars(select(Account).where(Account.id.in_(account_ids))).all()}

        total_debit = 0.0
        total_credit = 0.0
        for line in lines:
            account = accounts.get(line.account_id)
            if account is None or account.is_deleted:
                raise ApiError("One or more selected accounts do not exist.", code="invalid_reference", status_code=400)
            if account.is_model_b_only:
                raise ApiError(
                    f"'{account.name}' is a Model B account -- Model B is deferred entirely in v1.",
                    code="model_b_deferred",
                    status_code=400,
                )
            if bool(line.debit) == bool(line.credit):
                raise ApiError(
                    "Each line must have exactly one of debit or credit set (not both, not neither).",
                    code="invalid_line",
                    status_code=400,
                )
            if account.requires_unit and line.unit_id is None:
                raise ApiError(
                    f"'{account.name}' requires a unit on every posting (Appendix A [D]).",
                    code="unit_required",
                    status_code=400,
                )
            total_debit += line.debit
            total_credit += line.credit

        if round(total_debit, 2) != round(total_credit, 2):
            raise ApiError(
                f"Entry doesn't balance: debits {total_debit:.2f} vs. credits {total_credit:.2f}.",
                code="entry_unbalanced",
                status_code=400,
            )

    @staticmethod
    def _attach_lines(db: Session, rows: list[JournalEntry]) -> None:
        if not rows:
            return
        entry_ids = [r.id for r in rows]
        lines = list(
            db.scalars(
                select(JournalEntryLine)
                .where(JournalEntryLine.journal_entry_id.in_(entry_ids), JournalEntryLine.is_deleted.is_(False))
            ).all()
        )

        account_ids = {line.account_id for line in lines}
        accounts = {a.id: a for a in db.scalars(select(Account).where(Account.id.in_(account_ids))).all()}
        unit_ids = {line.unit_id for line in lines if line.unit_id}
        units = {u.id: u.unit_code for u in db.scalars(select(Unit).where(Unit.id.in_(unit_ids))).all()} if unit_ids else {}

        for line in lines:
            account = accounts.get(line.account_id)
            line.account_code = account.code if account else None
            line.account_name = account.name if account else None
            line.unit_code = units.get(line.unit_id) if line.unit_id else None

        lines_by_entry: dict[uuid.UUID, list[JournalEntryLine]] = {}
        for line in lines:
            lines_by_entry.setdefault(line.journal_entry_id, []).append(line)
        for r in rows:
            r.lines = lines_by_entry.get(r.id, [])
