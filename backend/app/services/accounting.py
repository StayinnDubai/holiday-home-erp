import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, paginate
from app.models.accounting import (
    Account,
    BankAccount,
    BankAccountColumn,
    BankStatementEntry,
    Cheque,
)
from app.models.foundation import Currency
from app.models.master_data import Counterparty
from app.schemas.accounting import (
    AccountCreate,
    AccountUpdate,
    BankAccountColumnCreate,
    BankAccountColumnUpdate,
    BankAccountCreate,
    BankAccountUpdate,
    BankStatementEntryCreate,
    BankStatementEntryUpdate,
    ChequeCreate,
    ChequeUpdate,
)
from app.services.audit import AuditService


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
        if params.sort_by == "parent_account_code":
            parent = aliased(Account)
            stmt = stmt.outerjoin(parent, parent.id == Account.parent_account_id)
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
        if params.sort_by == "counterparty_name":
            stmt = stmt.join(Counterparty, Counterparty.id == Cheque.counterparty_id)
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

        for field, value in data.items():
            setattr(row, field, value)

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
        for r in rows:
            r.counterparty_name = counterparties.get(r.counterparty_id)


class BankAccountService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BankAccount], int]:
        stmt = select(BankAccount).where(BankAccount.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(BankAccount.code.ilike(f"%{params.q}%") | BankAccount.account_name.ilike(f"%{params.q}%"))
        if params.sort_by == "bank_name":
            stmt = stmt.join(Counterparty, Counterparty.id == BankAccount.bank_id)
            col = Counterparty.name
        elif params.sort_by == "chart_account_code":
            stmt = stmt.outerjoin(Account, Account.id == BankAccount.chart_account_id)
            col = Account.code
        elif params.sort_by == "currency_name":
            stmt = stmt.join(Currency, Currency.id == BankAccount.currency_id)
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
        if params.sort_by == "bank_account_label":
            stmt = stmt.join(BankAccount, BankAccount.id == BankAccountColumn.bank_account_id)
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
        col = _sort_col(BankStatementEntry, params.sort_by, BankStatementEntry.created_at)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

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
