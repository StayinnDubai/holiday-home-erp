import { EntityPageConfig, SelectOption } from '../../shared/crud/entity-page-config.model';

/** Year-built is a bounded, pick-from-a-list field rather than a free number --
 * generated once here rather than hard-coded, so it never needs manual upkeep. */
function yearOptions(from = 1970): SelectOption[] {
  const currentYear = new Date().getFullYear();
  const years: SelectOption[] = [];
  for (let y = currentYear + 2; y >= from; y--) {
    years.push({ label: String(y), value: String(y) });
  }
  return years;
}

/** Header fields (plan §3.2 `building` table / doc §1.3), plus `unit_count` -- a
 * backend-computed column (count of units with this building_id) proving the
 * reverse of "one building per unit": a building holds one-or-more units.
 *
 * Restrictions, access rules, parking, move-in permit requirements and portal
 * credentials all live on the header (doc §1.3: "the place where access rules,
 * permit requirements and restrictions actually live"), mostly hidden from the grid
 * (showInGrid: false) since they're descriptive/reference fields, not things you'd
 * scan a list by. Contacts, amenities and deposits/fees are genuinely repeatable
 * per building, so they get their own pages (BUILDING_CONTACTS_CONFIG etc. below)
 * rather than being crammed into this form. */
export const BUILDINGS_CONFIG: EntityPageConfig = {
  title: 'Buildings',
  subtitle: 'Everything true of a building rather than a unit (doc §1.3) -- access rules, permits and restrictions live here.',
  resourcePath: 'buildings',
  fields: [
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'unit_count', label: 'Units', type: 'number', showInForm: false, gridWidth: 90 },
    { key: 'developer', label: 'Developer', type: 'text' },
    { key: 'community', label: 'Community', type: 'text' },
    { key: 'area', label: 'Area', type: 'text' },
    { key: 'address', label: 'Address', type: 'text', showInGrid: false },
    { key: 'makani', label: 'Makani', type: 'text', gridWidth: 130 },
    { key: 'plot_number', label: 'Plot number', type: 'text', showInGrid: false },
    { key: 'floors', label: 'Floors', type: 'number', gridWidth: 100 },
    { key: 'year_built', label: 'Year built', type: 'select', options: yearOptions(), gridWidth: 110 },

    // ---- Restrictions (doc §1.3 "Restrictions"): a gate above the landlord's permission ----
    {
      key: 'short_term_permitted',
      label: 'Short-term permitted',
      type: 'select',
      required: true,
      options: [
        { label: 'Yes', value: 'yes' },
        { label: 'No', value: 'no' },
        { label: 'Conditional', value: 'conditional' },
      ],
      gridWidth: 150,
    },
    {
      key: 'short_term_conditions',
      label: 'Conditions (if conditional)',
      type: 'textarea',
      showInGrid: false,
      visibleWhen: { field: 'short_term_permitted', equals: 'conditional' },
    },
    { key: 'party_noise_rules', label: 'Party / noise rules', type: 'textarea', showInGrid: false },
    { key: 'pet_rules', label: 'Pet rules', type: 'textarea', showInGrid: false },

    // ---- Access rules (doc §1.3 "Access rules") ----
    {
      key: 'access_rules',
      label: 'Access rules',
      type: 'textarea',
      showInGrid: false,
    },

    // ---- Move-in permit requirements (doc §1.3, feeds Move-in Permits module) ----
    { key: 'move_in_permit_required', label: 'Move-in permit required', type: 'boolean', gridWidth: 150 },
    { key: 'move_in_permit_trigger_events', label: 'Move-in permit: trigger events', type: 'textarea', showInGrid: false },
    { key: 'move_in_permit_lead_time_days', label: 'Move-in permit: lead time (days)', type: 'number', showInGrid: false },
    { key: 'move_in_permit_cost', label: 'Move-in permit: cost (AED)', type: 'number', showInGrid: false },
    { key: 'move_in_permit_deposit_amount', label: 'Move-in permit: deposit (AED)', type: 'number', showInGrid: false },
    { key: 'move_in_permit_deposit_refundable', label: 'Move-in permit: deposit refundable', type: 'boolean', showInGrid: false },
    { key: 'move_in_permit_documents_required', label: 'Move-in permit: documents required', type: 'textarea', showInGrid: false },
    { key: 'move_in_permit_checklist', label: 'Move-in permit: checklist', type: 'textarea', showInGrid: false },
    { key: 'move_in_permit_applied_by', label: 'Move-in permit: who applies', type: 'text', showInGrid: false },
    { key: 'move_in_permit_turnaround', label: 'Move-in permit: typical turnaround', type: 'text', showInGrid: false },

    // ---- Parking (doc §1.3 "Parking") ----
    { key: 'parking_allocation_basis', label: 'Parking: allocation basis', type: 'text', showInGrid: false },
    { key: 'parking_bays_per_unit', label: 'Parking: bays per unit', type: 'number', showInGrid: false },
    { key: 'parking_card_required', label: 'Parking: separate card required', type: 'boolean', showInGrid: false },
    { key: 'parking_cost', label: 'Parking: cost (AED)', type: 'number', showInGrid: false },
    { key: 'visitor_parking_rules', label: 'Parking: visitor rules', type: 'textarea', showInGrid: false },

    // ---- Service charges (doc §1.3: always the landlord's -- reference only) ----
    { key: 'service_charges_note', label: 'Service charges (reference only, never a cost)', type: 'textarea', showInGrid: false },

    // ---- Building portal / account credentials (doc §1.3) ----
    { key: 'portal_system_name', label: 'Portal: system name', type: 'text', showInGrid: false },
    { key: 'portal_username', label: 'Portal: username', type: 'text', showInGrid: false },
    { key: 'portal_reference_number', label: 'Portal: reference number', type: 'text', showInGrid: false },
    { key: 'portal_notes', label: 'Portal: notes', type: 'textarea', showInGrid: false },
  ],
};

/** doc §1.3 `BuildingContact` -- "the list your operations team needs at 11pm when a
 * guest is locked out." */
export const BUILDING_CONTACTS_CONFIG: EntityPageConfig = {
  title: 'Building Contacts',
  subtitle: 'Per-building contacts -- management, OA, security, technician, concierge, cleaning, parking (doc §1.3).',
  resourcePath: 'building-contacts',
  fields: [
    {
      key: 'building_id',
      label: 'Building',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'buildings',
      relationLabelKey: 'name',
      showInGrid: false,
    },
    { key: 'building_name', label: 'Building', type: 'text', showInForm: false, gridWidth: 180 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 180 },
    {
      key: 'role',
      label: 'Role',
      type: 'select',
      options: [
        { label: 'Building management', value: 'building_management' },
        { label: 'Owners association', value: 'owners_association' },
        { label: 'Security', value: 'security' },
        { label: 'Technician', value: 'technician' },
        { label: 'Concierge', value: 'concierge' },
        { label: 'Cleaning', value: 'cleaning' },
        { label: 'Parking', value: 'parking' },
        { label: 'Other', value: 'other' },
      ],
      gridWidth: 170,
    },
    { key: 'company', label: 'Company', type: 'text', gridWidth: 160 },
    { key: 'phone', label: 'Phone', type: 'text', gridWidth: 140 },
    { key: 'email', label: 'Email', type: 'text', showInGrid: false },
    { key: 'working_hours', label: 'Working hours', type: 'text', showInGrid: false },
    { key: 'out_of_hours_contact', label: 'Out-of-hours contact', type: 'text', showInGrid: false },
    { key: 'notes', label: 'Notes', type: 'textarea', showInGrid: false },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 90 },
  ],
};

/** doc §1.3 `BuildingAmenity` -- "feeds the guest information pack and the check-in
 * task, so it is worth holding properly rather than as one free-text blob."
 * Temporary closure records (date range + reason) are deferred -- see the model's
 * docstring for why. */
export const BUILDING_AMENITIES_CONFIG: EntityPageConfig = {
  title: 'Building Amenities',
  subtitle: 'Pool, gym, sauna, kids’ area, BBQ, co-working... (doc §1.3). Feeds the guest information pack and check-in task.',
  resourcePath: 'building-amenities',
  fields: [
    {
      key: 'building_id',
      label: 'Building',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'buildings',
      relationLabelKey: 'name',
      showInGrid: false,
    },
    { key: 'building_name', label: 'Building', type: 'text', showInForm: false, gridWidth: 180 },
    { key: 'name', label: 'Amenity', type: 'text', required: true, gridWidth: 180 },
    { key: 'operating_hours', label: 'Operating hours', type: 'textarea', gridWidth: 200 },
    {
      key: 'access_method',
      label: 'Access method',
      type: 'select',
      options: [
        { label: 'Card', value: 'card' },
        { label: 'Code', value: 'code' },
        { label: 'Key', value: 'key' },
        { label: 'Open', value: 'open' },
      ],
      gridWidth: 130,
    },
    { key: 'booking_required', label: 'Booking required', type: 'boolean', gridWidth: 130 },
    { key: 'guest_access_permitted', label: 'Guest access permitted', type: 'boolean', gridWidth: 150 },
    { key: 'rules_notes', label: 'Rules and notes', type: 'textarea', showInGrid: false },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 90 },
  ],
};

/** doc §1.3 "Deposits and fees held with building management" -- refundable
 * deposits and non-refundable fees, tracked separately "because only one comes
 * back." Feeds the same deposit recovery report as utility and landlord deposits
 * (doc §1.1) once that report is built. */
export const BUILDING_DEPOSITS_CONFIG: EntityPageConfig = {
  title: 'Building Deposits & Fees',
  subtitle: 'Refundable deposits and non-refundable fees held with building management (doc §1.3) -- tracked separately because only one comes back.',
  resourcePath: 'building-deposits',
  fields: [
    {
      key: 'building_id',
      label: 'Building',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'buildings',
      relationLabelKey: 'name',
      showInGrid: false,
    },
    { key: 'building_name', label: 'Building', type: 'text', showInForm: false, gridWidth: 160 },
    {
      key: 'type',
      label: 'Type',
      type: 'select',
      required: true,
      options: [
        { label: 'Refundable deposit', value: 'refundable_deposit' },
        { label: 'Non-refundable fee', value: 'non_refundable_fee' },
      ],
      gridWidth: 160,
    },
    { key: 'description', label: 'Description', type: 'text', required: true, gridWidth: 220 },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true, gridWidth: 130 },
    { key: 'date', label: 'Date', type: 'date', gridWidth: 120 },
    { key: 'reference', label: 'Reference', type: 'text', showInGrid: false },
    { key: 'refundable', label: 'Refundable', type: 'boolean', gridWidth: 110 },
    { key: 'condition_for_release', label: 'Condition for release', type: 'textarea', showInGrid: false },
    {
      key: 'recovery_status',
      label: 'Recovery status',
      type: 'select',
      required: true,
      options: [
        { label: 'Outstanding', value: 'outstanding' },
        { label: 'Recovered', value: 'recovered' },
        { label: 'Forfeited', value: 'forfeited' },
        { label: 'Not applicable', value: 'not_applicable' },
      ],
      gridWidth: 140,
    },
  ],
};
