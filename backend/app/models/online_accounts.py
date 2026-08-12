"""Online Accounts -- a standalone credential register, generalizing the pattern
already used by Building.portal_* (backend/app/models/master_data.py) -- that one
is scoped to a single building and deliberately has no password field. This module
is explicit, broader (any service, any related record), and does store a password:
this codebase has no encryption/secrets layer anywhere yet, so it's kept as plain
text like every other string field here -- a real limitation, not an oversight.
"""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditableRecord, Base


class OnlineAccount(AuditableRecord, Base):
    __tablename__ = "online_account"

    service_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))  # e.g. Utility portal, OTA, Bank
    # Free-text label, not a real polymorphic FK -- this app has no generic
    # "pick any record" selector, so this stays a plain string (e.g. "Building -
    # Marina Tower"), same low-friction spirit as other free-text reference fields.
    related_to: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500))
    username: Mapped[str | None] = mapped_column(String(255))
    password: Mapped[str | None] = mapped_column(String(255))
    sign_in_method: Mapped[str | None] = mapped_column(String(20))  # password|two_factor|sso|api_key|other
    recovery_email: Mapped[str | None] = mapped_column(String(255))
    comments: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
