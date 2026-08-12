from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.routers import (
    accounts,
    attachments,
    audit_log,
    bank_account_columns,
    bank_accounts,
    bank_statement_entries,
    building_amenities,
    building_contacts,
    building_deposits,
    buildings,
    cheques,
    comments,
    company,
    counterparties,
    counterparty_groups,
    currencies,
    ejari_registrations,
    inventory_items,
    inventory_movements,
    reference_lists,
    settings_,
    tenancy_contracts,
    unit_spaces,
    units,
)

app = FastAPI(
    title="Holiday Home ERP API",
    version="0.1.0",
    description=(
        "v1 scope: no auth/roles yet (every endpoint is open) and no automated tests -- "
        "see the build plan §7 for what's deferred and why."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

API_PREFIX = "/api/v1"
app.include_router(reference_lists.router, prefix=API_PREFIX)
app.include_router(settings_.router, prefix=API_PREFIX)
app.include_router(attachments.router, prefix=API_PREFIX)
app.include_router(comments.router, prefix=API_PREFIX)
app.include_router(audit_log.router, prefix=API_PREFIX)
app.include_router(buildings.router, prefix=API_PREFIX)
app.include_router(building_contacts.router, prefix=API_PREFIX)
app.include_router(building_amenities.router, prefix=API_PREFIX)
app.include_router(building_deposits.router, prefix=API_PREFIX)
app.include_router(counterparties.router, prefix=API_PREFIX)
app.include_router(counterparty_groups.router, prefix=API_PREFIX)
app.include_router(units.router, prefix=API_PREFIX)
app.include_router(unit_spaces.router, prefix=API_PREFIX)
app.include_router(tenancy_contracts.router, prefix=API_PREFIX)
app.include_router(ejari_registrations.router, prefix=API_PREFIX)
app.include_router(cheques.router, prefix=API_PREFIX)
app.include_router(bank_accounts.router, prefix=API_PREFIX)
app.include_router(bank_account_columns.router, prefix=API_PREFIX)
app.include_router(bank_statement_entries.router, prefix=API_PREFIX)
app.include_router(company.router, prefix=API_PREFIX)
app.include_router(currencies.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(inventory_items.router, prefix=API_PREFIX)
app.include_router(inventory_movements.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
