"""Master data (plan §3.2), scoped for this pass to exactly the three modules being
built end-to-end: Building, Counterparty (landlords), Unit, and the join table between
them. Everything else in the original plan's master-data section (unit spaces,
ownership shares/effective-dating, handover inspections, etc.) is deferred until its
own module is built -- this is deliberately the header-only slice.
"""
import uuid
from datetime import date
from datetime import date as _date  # BuildingDeposit has a field literally named
# `date`, which shadows the `date` type inside its own class body -- alias avoids it.

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditableRecord, Base


class Building(AuditableRecord, Base):
    """Plan §3.2 `building` (doc §1.3) -- "everything true of a building rather than
    a unit... the place where access rules, permit requirements and restrictions
    actually live." A building holds one-or-more units (the reverse of
    Unit.building_id being mandatory and singular).

    Restrictions, access rules, parking, move-in permit requirements and portal
    credentials are kept as flat fields on the header rather than split into further
    child tables -- each is a small number of mostly-scalar values (unlike Contacts/
    Amenities/Deposits below, which are genuinely repeatable and get their own
    tables). `short_term_permitted` is a gate above the landlord's permission (doc
    §1.4 `holiday_home_permitted`): where this is 'no', the unit is blocked from the
    short-term product line even if the head lease allows it -- enforcement lands
    with the reservations/product-line-conversion modules, this column just carries
    the fact now so nothing needs to be retrofitted onto it later.
    """

    __tablename__ = "building"

    name: Mapped[str] = mapped_column(String(255))
    developer: Mapped[str | None] = mapped_column(String(255))
    community: Mapped[str | None] = mapped_column(String(255))
    area: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    makani: Mapped[str | None] = mapped_column(String(50))
    plot_number: Mapped[str | None] = mapped_column(String(50))
    floors: Mapped[int | None]
    year_built: Mapped[int | None]

    # ---- Restrictions (doc §1.3 "Restrictions") ----
    short_term_permitted: Mapped[str] = mapped_column(String(20), default="yes")  # yes | no | conditional
    short_term_conditions: Mapped[str | None] = mapped_column(Text)  # free text, when 'conditional'
    party_noise_rules: Mapped[str | None] = mapped_column(Text)
    pet_rules: Mapped[str | None] = mapped_column(Text)

    # ---- Access rules (doc §1.3 "Access rules") ----
    access_rules: Mapped[str | None] = mapped_column(Text)

    # ---- Move-in permit requirements (doc §1.3, feeds 1.7) ----
    move_in_permit_required: Mapped[bool] = mapped_column(Boolean, default=False)
    move_in_permit_trigger_events: Mapped[str | None] = mapped_column(Text)
    move_in_permit_lead_time_days: Mapped[int | None]
    move_in_permit_cost: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    move_in_permit_deposit_amount: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    move_in_permit_deposit_refundable: Mapped[bool | None] = mapped_column(Boolean)
    move_in_permit_documents_required: Mapped[str | None] = mapped_column(Text)
    move_in_permit_checklist: Mapped[str | None] = mapped_column(Text)
    move_in_permit_applied_by: Mapped[str | None] = mapped_column(String(255))
    move_in_permit_turnaround: Mapped[str | None] = mapped_column(String(255))

    # ---- Parking (doc §1.3 "Parking") ----
    parking_allocation_basis: Mapped[str | None] = mapped_column(String(255))
    parking_bays_per_unit: Mapped[int | None]
    parking_card_required: Mapped[bool | None] = mapped_column(Boolean)
    parking_cost: Mapped[float | None] = mapped_column(Numeric(12, 2, asdecimal=False))
    visitor_parking_rules: Mapped[str | None] = mapped_column(Text)

    # ---- Service charges (doc §1.3: "always the landlord's" -- reference only, never a P&L cost) ----
    service_charges_note: Mapped[str | None] = mapped_column(Text)

    # ---- Building portal / account credentials (doc §1.3) ----
    portal_system_name: Mapped[str | None] = mapped_column(String(255))
    portal_username: Mapped[str | None] = mapped_column(String(255))
    portal_reference_number: Mapped[str | None] = mapped_column(String(100))
    portal_notes: Mapped[str | None] = mapped_column(Text)

    units: Mapped[list["Unit"]] = relationship(back_populates="building")


class BuildingContact(AuditableRecord, Base):
    """doc §1.3 `BuildingContact` -- "the list your operations team needs at 11pm
    when a guest is locked out." As many as needed per building."""

    __tablename__ = "building_contact"

    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255))
    # building management | owners association | security | technician | concierge | cleaning | parking | other
    role: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    working_hours: Mapped[str | None] = mapped_column(String(255))
    out_of_hours_contact: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BuildingAmenity(AuditableRecord, Base):
    """doc §1.3 `BuildingAmenity` -- "feeds the guest information pack and the
    check-in task, so it is worth holding properly rather than as one free-text
    blob." Temporary closure records (date range + reason) are deferred -- cheap to
    add as a child table later, not built now since nothing consumes them yet
    (no guest information pack / check-in task exists to feed).
    """

    __tablename__ = "building_amenity"

    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255))  # pool, gym, sauna, kids' area, BBQ, co-working...
    operating_hours: Mapped[str | None] = mapped_column(Text)
    access_method: Mapped[str | None] = mapped_column(String(20))  # card | code | key | open
    booking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    guest_access_permitted: Mapped[bool] = mapped_column(Boolean, default=True)
    rules_notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class BuildingDeposit(AuditableRecord, Base):
    """doc §1.3 "Deposits and fees held with building management" -- refundable
    deposits (renovation/fit-out, move-in) and non-refundable fees (access/parking
    card issue) tracked separately "because only one comes back." Feeds the same
    deposit recovery report as utility and landlord deposits (doc §1.1) once that
    report exists.
    """

    __tablename__ = "building_deposit"

    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30))  # refundable_deposit | non_refundable_fee
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False))
    date: Mapped[_date | None] = mapped_column(Date)
    reference: Mapped[str | None] = mapped_column(String(100))
    refundable: Mapped[bool] = mapped_column(Boolean, default=False)
    condition_for_release: Mapped[str | None] = mapped_column(Text)
    # outstanding | recovered | forfeited | not_applicable
    recovery_status: Mapped[str] = mapped_column(String(20), default="outstanding")


class CounterpartyGroup(AuditableRecord, Base):
    """Accounting > Counterparty Group -- a manually-maintained classification for
    counterparties (e.g. "Landlords - Downtown", "OTA channels", "Utility suppliers").
    Purely organisational: no commercial terms live here, same principle the doc
    already applies to the landlord record itself (doc §1.2 "no commercial terms are
    ever stored on a landlord").
    """

    __tablename__ = "counterparty_group"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    members: Mapped[list["Counterparty"]] = relationship(back_populates="group")


class Counterparty(AuditableRecord, Base):
    """Plan §3.2 `counterparty` (doc §2.6) -- single master for landlord/tenant/
    supplier/agent/OTA. `roles` is stored as a comma-separated string in this pass
    rather than a normalized roles table -- cheap now, easy to split later."""

    __tablename__ = "counterparty"

    code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20))  # individual | company
    roles: Mapped[str | None] = mapped_column(String(255))
    trn: Mapped[str | None] = mapped_column(String(50))
    emirates_id: Mapped[str | None] = mapped_column(String(50))
    hold_flag: Mapped[bool] = mapped_column(default=False)
    group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("counterparty_group.id"))

    unit_links: Mapped[list["UnitLandlord"]] = relationship(back_populates="landlord")
    group: Mapped["CounterpartyGroup | None"] = relationship(back_populates="members")


class Unit(AuditableRecord, Base):
    """Plan §3.2 `unit` -- header fields only. Exactly one building (mandatory FK);
    one-or-more landlords via `UnitLandlord` (doc §1.1: a unit may have several
    co-owners). `unit_code` is server-generated (NumberingService), never client-set.

    `floor_number`/`apartment_number` are the physical identifiers on the door and
    the title deed -- distinct from `unit_code` (this system's own sequential ID)
    and from `unit_name` (a free-text label). Areas are in square metres throughout
    (not sqft), matching the title deed / Ejari convention in Dubai.
    """

    __tablename__ = "unit"

    unit_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    unit_name: Mapped[str] = mapped_column(String(255))
    building_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building.id"), nullable=False)
    type: Mapped[str | None] = mapped_column(String(20))
    property_type: Mapped[str | None] = mapped_column(String(30))  # apartment | villa | townhouse | penthouse | other
    floor_number: Mapped[str | None] = mapped_column(String(50))
    apartment_number: Mapped[str | None] = mapped_column(String(50))
    parking_number: Mapped[str | None] = mapped_column(String(50))
    bathrooms: Mapped[int | None]
    max_occupancy: Mapped[int | None]
    area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))
    suite_area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))
    has_balcony: Mapped[bool] = mapped_column(Boolean, default=False)
    balcony_area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2, asdecimal=False))
    furnished_status: Mapped[str | None] = mapped_column(String(20))  # furnished | unfurnished
    title_deed_number: Mapped[str | None] = mapped_column(String(100))
    dewa_premises_number: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="active")
    handover_date: Mapped[date | None] = mapped_column(Date)
    first_live_date: Mapped[date | None] = mapped_column(Date)

    building: Mapped[Building] = relationship(back_populates="units")
    landlord_links: Mapped[list["UnitLandlord"]] = relationship(back_populates="unit", cascade="all, delete-orphan")
    spaces: Mapped[list["UnitSpace"]] = relationship(back_populates="unit", cascade="all, delete-orphan")


class UnitLandlord(Base):
    """Many-to-many join, unit <-> landlord (doc §1.1 "a unit may be held by several
    landlords"). No soft-delete/timestamps -- this pass keeps it a plain link row;
    ownership share % and effective-dating (plan's original `UnitOwnership`) are
    deferred until Model B / investor reporting actually needs them."""

    __tablename__ = "unit_landlord"
    __table_args__ = (UniqueConstraint("unit_id", "landlord_id", name="uq_unit_landlord"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit.id"), nullable=False)
    landlord_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("counterparty.id"), nullable=False)

    unit: Mapped[Unit] = relationship(back_populates="landlord_links")
    landlord: Mapped[Counterparty] = relationship(back_populates="unit_links")


class UnitSpace(AuditableRecord, Base):
    """Plan's original `UnitSpace` (doc §1.1) -- one record per physical space in a
    unit (bedroom, bathroom, living room, kitchen, laundry area, balcony, storage...),
    "so a physical verification can be done room by room." Deferred until now
    because nothing consumed it yet; kept deliberately simple (no sort order / space
    code / active flag) versus the doc's fuller spec, since the only consumer today
    is a plain add/edit/delete list on the unit's edit view, not room-level
    inventory or asset tracking.
    """

    __tablename__ = "unit_space"

    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("unit.id"), nullable=False)
    # bedroom | bathroom | living_room | kitchen | laundry_area | balcony | storage | dining_room | office | other
    space_type: Mapped[str] = mapped_column(String(30))
    name: Mapped[str | None] = mapped_column(String(255))  # e.g. "Bedroom 1", optional
    notes: Mapped[str | None] = mapped_column(Text)

    unit: Mapped[Unit] = relationship(back_populates="spaces")
