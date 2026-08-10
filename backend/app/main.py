from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.routers import attachments, audit_log, buildings, comments, counterparties, reference_lists, settings_, units

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
app.include_router(counterparties.router, prefix=API_PREFIX)
app.include_router(units.router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
