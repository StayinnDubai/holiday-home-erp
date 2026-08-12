"""Seeds a freshly-migrated database with the data v1 cannot run without: the
single Entity row and the Chart of Accounts (Appendix A). Idempotent -- safe to
run more than once.

Usage (from backend/, with DATABASE_URL pointing at a running Postgres):
    python -m app.seed.run
"""
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.accounting import Account
from app.models.foundation import Currency, Entity, ReferenceListItem
from app.seed.chart_of_accounts import ACCOUNTS, CONTROL_ACCOUNT_CODES

# Settings > Currencies -- multi-currency support (v1: manually maintained list).
CURRENCIES = [
    ("001", "AED", "UAE Dirham"),
    ("002", "USD", "US Dollar"),
    ("003", "AMD", "Armenian Dram"),
]

# doc §1.1: confirmed block-type availability -- owner stay, renovation, staff use,
# contract gap, deep clean are unavailable (excluded from adjusted occupancy);
# maintenance and marketing/photography default unavailable but are editable;
# same-day turnover gap is available.
BLOCK_TYPES = [
    ("owner_stay", "Owner stay", False),
    ("renovation", "Renovation", False),
    ("staff_use", "Staff use", False),
    ("contract_gap", "Contract gap", False),
    ("deep_clean", "Deep clean", False),
    ("maintenance", "Maintenance", False),
    ("marketing_photography", "Marketing / photography", False),
    ("turnover_gap", "Turnover gap (same-day)", True),
]


def seed_currencies(db) -> None:
    existing_codes = set(db.execute(select(Currency.code)).scalars().all())
    created = 0
    for code, name, full_name in CURRENCIES:
        if code in existing_codes:
            continue
        db.add(Currency(code=code, name=name, full_name=full_name))
        created += 1
    db.flush()
    print(f"Seeded {created} new currencies ({len(CURRENCIES) - created} already present).")


def seed_entity(db) -> Entity:
    entity = db.execute(select(Entity)).scalars().first()
    if entity is None:
        aed_id = db.execute(select(Currency.id).where(Currency.name == "AED")).scalars().first()
        entity = Entity(legal_name="Holiday Home ERP Co.", base_currency_id=aed_id, timezone="Asia/Dubai")
        db.add(entity)
        db.flush()
        print("Created Entity row.")
    return entity


def seed_accounts(db) -> None:
    existing_codes = set(db.execute(select(Account.code)).scalars().all())
    created = 0
    for code, name, account_type, normal_balance, requires_unit, is_model_b_only in ACCOUNTS:
        if code in existing_codes:
            continue
        db.add(
            Account(
                code=code,
                name=name,
                account_type=account_type,
                normal_balance=normal_balance,
                requires_unit=requires_unit,
                is_model_b_only=is_model_b_only,
                control_account=code in CONTROL_ACCOUNT_CODES,
            )
        )
        created += 1
    db.flush()
    print(f"Seeded {created} new accounts ({len(ACCOUNTS) - created} already present).")


def seed_block_types(db) -> None:
    existing = set(
        db.execute(select(ReferenceListItem.code).where(ReferenceListItem.list_name == "block_type")).scalars().all()
    )
    created = 0
    for i, (code, label, is_available) in enumerate(BLOCK_TYPES):
        if code in existing:
            continue
        db.add(
            ReferenceListItem(
                list_name="block_type", code=code, label=label, is_available=is_available, sort_order=i
            )
        )
        created += 1
    db.flush()
    print(f"Seeded {created} new block types ({len(BLOCK_TYPES) - created} already present).")


def run() -> None:
    db = SessionLocal()
    try:
        seed_currencies(db)
        seed_entity(db)
        seed_accounts(db)
        seed_block_types(db)
        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
