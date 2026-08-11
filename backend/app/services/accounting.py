import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.pagination import PaginationParams, paginate
from app.models.accounting import Account, BankStatementLine, Cheque
from app.models.master_data import Counterparty
from app.schemas.accounting import (
    AccountCreate,
    AccountUpdate,
    BankStatementLineCreate,
    BankStatementLineUpdate,
    ChequeCreate,
    ChequeUpdate,
)
from app.services.audit import AuditService


def _sort_col(model, sort_by: str | None, default):
    if sort_by and hasattr(model, sort_by):
        return getattr(model, sort_by)
    return default


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


class BankStatementLineService:
    @staticmethod
    def list_page(db: Session, params: PaginationParams) -> tuple[list[BankStatementLine], int]:
        stmt = select(BankStatementLine).where(BankStatementLine.is_deleted.is_(False))
        if params.q:
            stmt = stmt.where(
                BankStatementLine.description.ilike(f"%{params.q}%")
                | BankStatementLine.ref_number.ilike(f"%{params.q}%")
                | BankStatementLine.account_name.ilike(f"%{params.q}%")
            )
        col = _sort_col(BankStatementLine, params.sort_by, BankStatementLine.date)
        stmt = stmt.order_by(col.asc() if params.sort_dir != "desc" else col.desc())
        return paginate(db, stmt, params)

    @staticmethod
    def get(db: Session, line_id: uuid.UUID) -> BankStatementLine:
        row = db.get(BankStatementLine, line_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement line not found.", code="not_found", status_code=404)
        return row

    @staticmethod
    def create(db: Session, payload: BankStatementLineCreate) -> BankStatementLine:
        row = BankStatementLine(**payload.model_dump())
        db.add(row)
        db.flush()
        AuditService.log(db, entity_type="bank_statement_line", entity_id=row.id, action="create")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def update(db: Session, line_id: uuid.UUID, payload: BankStatementLineUpdate) -> BankStatementLine:
        row = db.get(BankStatementLine, line_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement line not found.", code="not_found", status_code=404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        AuditService.log(db, entity_type="bank_statement_line", entity_id=row.id, action="update")
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def soft_delete(db: Session, line_id: uuid.UUID) -> None:
        row = db.get(BankStatementLine, line_id)
        if row is None or row.is_deleted:
            raise ApiError("Bank statement line not found.", code="not_found", status_code=404)
        row.is_deleted = True
        AuditService.log(db, entity_type="bank_statement_line", entity_id=row.id, action="delete")
        db.commit()
