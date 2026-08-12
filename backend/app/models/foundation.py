"""Foundation-layer tables (plan §3.1): company row, generic cross-cutting tables
(audit log, attachments, comments, numbering, reference lists, settings) used by
every other module. No app_user / auth tables here yet (deferred, plan §7).
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base, IdMixin, TimestampMixin


class Entity(IdMixin, TimestampMixin, Base):
    """Single company row (doc D-1: one legal entity, Dubai only). Every transactional
    table below carries entity_id, defaulted to this row's id, even though v1 only
    ever has one row -- see app/seed for how it's created.

    Settings > Company (doc §7): "legal entity, TRN, licence, logo, addresses,
    financial year 1 January - 31 December inclusive (confirmed), base currency,
    timezone." Logo is a generic Attachment (entity_type='company') rather than a
    column here, same as every other document in the system (doc §5.3). `address`
    is singular for now -- the doc's "addresses" (plural) isn't elaborated anywhere
    else, so splitting it into registered-vs-operating address is deferred until
    that distinction is actually needed rather than guessed at now.
    """

    __tablename__ = "entity"

    legal_name: Mapped[str] = mapped_column(String(255))
    brand_name: Mapped[str | None] = mapped_column(String(255))
    trn: Mapped[str | None] = mapped_column(String(50))
    vat_number: Mapped[str | None] = mapped_column(String(50))
    license_number: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(50))
    manager_name: Mapped[str | None] = mapped_column(String(255))
    date_of_registration: Mapped[date | None]
    # Free text for now -- one shareholder per line. A structured name/ownership-%
    # sub-entity is a natural next step but wasn't asked for; cheap to add later
    # without touching this column.
    shareholders: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    financial_year_start_month: Mapped[int] = mapped_column(default=1)  # doc §7: 1 Jan - 31 Dec
    base_currency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("currency.id"))  # doc §5.6: AED only in v1
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Dubai")

    base_currency: Mapped["Currency"] = relationship()


class Currency(AuditableRecord, Base):
    """Settings > Currencies -- multi-currency support. Manually-maintained list
    referenced by every "currency" field across the app (bank accounts, bank
    statement lines, the company's base currency) instead of a free-text 3-letter
    code, so a currency is picked from a list rather than typed. `code` is a
    manually-entered, unique 3-digit identifier (e.g. "001"); `name` is the
    short/ISO-ish code shown everywhere else (e.g. "AED"); `full_name` is the
    descriptive name (e.g. "UAE Dirham")."""

    __tablename__ = "currency"

    code: Mapped[str] = mapped_column(String(3), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(10))
    full_name: Mapped[str] = mapped_column(String(100))
    # Spot rate to the company's base currency (Entity.base_currency_id) -- current
    # value only, no rate history (nothing in this codebase has a time-series
    # pattern to mirror yet). Null means "not configured," not "1.0" -- stays honest
    # about incompleteness rather than silently assuming parity. Display/foundation
    # only in v1: JournalEntryLine has no currency field, so the GL itself stays
    # single-currency -- this doesn't retrofit conversion into postings/reports.
    rate_to_base: Mapped[float | None] = mapped_column(Numeric(18, 6, asdecimal=False))


# doc §5.7: VAT treatment options. `reverse_charge` only makes real accounting sense
# on the purchase/import side (see posting_rules/tax.py) -- kept here as a shared
# constant rather than duplicated in both accounting.py posting modules.
TAX_TREATMENTS = ("standard", "exempt", "zero", "reverse_charge")


class TaxCode(AuditableRecord, Base):
    """Settings > Tax Codes (doc §5.7) -- central VAT configuration: rate, treatment,
    effective dates. Never hard-coded 5% -- Bill/Invoice pick a TaxCode and store
    their own `tax_amount` (entered/computed client-side from `amount * rate`, not
    server-derived, matching every other numeric field in this codebase). Posting
    the VAT itself is posting_rules/tax.py's job, not this model's."""

    __tablename__ = "tax_code"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    rate: Mapped[float] = mapped_column(Numeric(6, 3, asdecimal=False), default=0)
    treatment: Mapped[str] = mapped_column(String(20), default="standard")  # one of TAX_TREATMENTS
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class AssetCategory(AuditableRecord, Base):
    """Settings > Asset Categories -- fixed-asset depreciation setup. Pure reference
    data in v1: there's no Fixed Asset Register tracking individual assets yet, so
    nothing posts depreciation against these categories -- they exist so that
    register can be configured against real categories once it's built, same as the
    doc's own note that "v1 posting logic implements straight-line only... unused"."""

    __tablename__ = "asset_category"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    useful_life_months: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(20), default="linear")  # linear|reducing_balance|sum_of_years|custom
    residual_pct: Mapped[float | None] = mapped_column(Numeric(5, 2, asdecimal=False))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CostType(AuditableRecord, Base):
    """Settings > Cost Categories (doc §7.8 describes a two-level type/subtype tree,
    kept flat here for v1). Pure reference data -- classifies ongoing operational
    costs (distinct from Setup Cost Types, a separate one-time-setup-cost concept
    not built in this pass)."""

    __tablename__ = "cost_type"

    type: Mapped[str] = mapped_column(String(100))
    subtype: Mapped[str | None] = mapped_column(String(100))
    direct_or_overhead: Mapped[str] = mapped_column(String(20), default="direct")  # direct|overhead
    recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(IdMixin, Base):
    """Immutable change log (doc §5.2). Written by app.services.audit, never edited.
    `changed_by` is nullable/unused until auth exists (plan §7).
    """

    __tablename__ = "audit_log"

    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    field: Mapped[str | None] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(30))  # create | update | delete | status_change
    reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[str | None] = mapped_column(String(255))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attachment(IdMixin, TimestampMixin, Base):
    """Generic file attachment, linkable to any entity by (entity_type, entity_id) --
    doc §5.3. Local disk storage in v1; file_path is relative to settings.upload_dir.

    `document_name` is a user-editable display label, separate from
    `original_filename` (the immutable name of the file as uploaded) -- it defaults
    to the filename at upload time but can be renamed afterwards without touching
    the underlying file, which is what "edit" means for an attachment in v1 (the
    file itself isn't replaced/versioned; re-upload creates a new attachment).
    """

    __tablename__ = "attachment"

    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    document_name: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(100))
    document_type: Mapped[str | None] = mapped_column(String(100))
    issue_date: Mapped[date | None]
    expiry_date: Mapped[date | None] = mapped_column(index=True)  # feeds the alert engine later


class Comment(IdMixin, TimestampMixin, Base):
    """Threaded comment log, generic per entity (doc §1.1 "Comments" / separate from
    the audit trail: audit records *what* changed, comments record *why*).
    """

    __tablename__ = "comment"

    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    author_name: Mapped[str] = mapped_column(String(255))  # free text until auth exists
    text: Mapped[str] = mapped_column(Text)


class DocumentSequence(IdMixin, Base):
    """Configurable sequential numbering per document type (doc §5.4). One row per
    doc_type (+ year, if the series resets yearly). Advanced atomically by
    app.services.numbering.NumberingService.
    """

    __tablename__ = "document_sequence"
    __table_args__ = (UniqueConstraint("doc_type", "year", name="uq_document_sequence_type_year"),)

    doc_type: Mapped[str] = mapped_column(String(50), index=True)  # e.g. 'unit', 'invoice', 'journal'
    prefix: Mapped[str] = mapped_column(String(20), default="")
    next_number: Mapped[int] = mapped_column(default=1)
    reset_cycle: Mapped[str] = mapped_column(String(20), default="never")  # never | yearly
    year: Mapped[int | None]  # populated only when reset_cycle='yearly'


class ReferenceListItem(AuditableRecord, Base):
    """Every "list maintained by you" from doc §7.4 lives here as data, never as a
    hard-coded enum: unit_type, unit_space_type, block_type (+available flag),
    utility_type, task_type, document_type, cancellation_policy, amenity_type,
    unit_group_type, tag, insurance_policy_type, counterparty_role.
    """

    __tablename__ = "reference_list_item"
    __table_args__ = (UniqueConstraint("list_name", "code", name="uq_reference_list_item_list_code"),)

    list_name: Mapped[str] = mapped_column(String(50), index=True)
    code: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(255))
    # Only meaningful for list_name='block_type' (doc §1.1): does this block type count
    # as available for the "adjusted occupancy" measure?
    is_available: Mapped[bool | None]
    sort_order: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(default=True)


class Setting(IdMixin, TimestampMixin, Base):
    """Key/value config store for thresholds and rates that must never be hard-coded
    (doc: "never a constant in code" appears repeatedly -- e.g. asset capitalisation
    threshold, cheque-deposit-reminder days, Tourism Dirham rate, alert horizons).
    Value is stored as text; callers parse to the type they expect.
    """

    __tablename__ = "setting"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
