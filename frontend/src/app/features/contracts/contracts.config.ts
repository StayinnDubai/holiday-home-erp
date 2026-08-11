import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { UNITS_CONFIG } from '../units/units.config';
import { COUNTERPARTIES_CONFIG } from '../counterparties/counterparties.config';

/** Header fields (doc §1.4 "Contract" object). One unit per contract (Q178); co-owners
 * go on `landlord_ids` the same way Units does it (doc §1.1) -- per-party share %/role/
 * payee flag is deferred until Model B/payment-schedule generation actually needs it,
 * same simplification the Units module already made for `UnitLandlord`.
 *
 * `renewal_of_id` is a self-relation: a renewal is a brand new contract row, never an
 * edit to the old one (doc "Renewal creates a new contract, never an amendment", Q151) --
 * the backend also blocks editing unit/start/end date once a contract is Active.
 *
 * The Ejari registration record is deliberately a separate page (EJARI_REGISTRATIONS_CONFIG
 * below), not fields folded into this form -- the doc's own design principle is that it's
 * a verbatim transcription of the certificate that may legitimately diverge from the
 * contract, not a second copy of it (doc §1.4 "design principle"). POA and the payment-
 * schedule/cheque-generation workflow stay deferred to the Accounting-core milestone. */
export const TENANCY_CONTRACTS_CONFIG: EntityPageConfig = {
  title: 'Tenancy Contracts',
  subtitle: 'Inbound lease, company ← landlord (doc §1.4). One unit per contract. Ejari registration is its own page once a contract exists.',
  resourcePath: 'tenancy-contracts',
  fields: [
    { key: 'contract_number', label: 'Contract #', type: 'text', showInForm: false, gridWidth: 130 },
    {
      key: 'unit_id',
      label: 'Unit',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'units',
      relationLabelKey: 'unit_name',
      relationCreateFields: UNITS_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'unit_code', label: 'Unit', type: 'text', showInForm: false, gridWidth: 100 },
    { key: 'unit_name', label: 'Unit name', type: 'text', showInForm: false, showInGrid: false },
    {
      key: 'landlord_ids',
      label: 'Landlords',
      type: 'relation-multiselect',
      required: true,
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'landlord_names', label: 'Landlords', type: 'text', showInForm: false, gridWidth: 200 },
    {
      key: 'contract_type',
      label: 'Type',
      type: 'select',
      options: [
        { label: 'New', value: 'new' },
        { label: 'Renewal', value: 'renewal' },
      ],
      gridWidth: 100,
    },
    {
      key: 'renewal_of_id',
      label: 'Renewal of (predecessor contract)',
      type: 'relation-select',
      relationResourcePath: 'tenancy-contracts',
      relationLabelKey: 'contract_number',
      showInGrid: false,
    },
    { key: 'renewal_of_contract_number', label: 'Renewal of', type: 'text', showInForm: false, showInGrid: false },
    { key: 'renewed_by_contract_number', label: 'Renewed by', type: 'text', showInForm: false, showInGrid: false },
    {
      key: 'gap_days',
      label: 'Uncovered gap (days)',
      type: 'number',
      showInForm: false,
      gridWidth: 150,
      gridValueFormatter: (v) => (v == null ? '' : String(v)),
    },
    { key: 'start_date', label: 'Start date', type: 'date', required: true, gridWidth: 120 },
    { key: 'end_date', label: 'End date', type: 'date', required: true, gridWidth: 120 },
    { key: 'total_annual_rent', label: 'Annual rent (AED)', type: 'number', required: true, gridWidth: 150 },
    { key: 'instalment_count', label: 'Instalments', type: 'number', showInGrid: false },
    {
      key: 'payment_method',
      label: 'Payment method',
      type: 'select',
      options: [
        { label: 'Cheque', value: 'cheque' },
        { label: 'Transfer', value: 'transfer' },
      ],
      showInGrid: false,
    },
    { key: 'security_deposit_amount', label: 'Security deposit (AED)', type: 'number', showInGrid: false },
    { key: 'agency_fee_amount', label: 'Agency fee (AED)', type: 'number', showInGrid: false },
    { key: 'agency_fee_vat_applicable', label: 'Agency fee VAT applicable', type: 'boolean', showInGrid: false },
    { key: 'notice_period_days', label: 'Notice period (days)', type: 'number', showInGrid: false },
    {
      key: 'sublease_permitted',
      label: 'Sublease permitted',
      type: 'select',
      required: true,
      options: [
        { label: 'Yes', value: 'yes' },
        { label: 'No', value: 'no' },
      ],
      gridWidth: 140,
    },
    {
      key: 'holiday_home_permitted',
      label: 'Holiday-home permitted',
      type: 'select',
      required: true,
      options: [
        { label: 'Yes', value: 'yes' },
        { label: 'No', value: 'no' },
      ],
      gridWidth: 160,
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Active', value: 'active' },
        { label: 'Expired', value: 'expired' },
        { label: 'Terminated', value: 'terminated' },
        { label: 'Superseded', value: 'superseded' },
      ],
      gridWidth: 110,
    },
  ],
};

/** doc §1.4 `EjariRegistration` -- a transcription of the certificate exactly as
 * registered, stored verbatim per field even where it diverges from the contract
 * above (that divergence is flagged by `variance_warnings`, computed by the backend
 * on every read, never auto-corrected). One registration per contract (Q183). */
export const EJARI_REGISTRATIONS_CONFIG: EntityPageConfig = {
  title: 'Ejari Registrations',
  subtitle: 'Certificate as registered (doc §1.4) — verbatim, even where it diverges from the contract. Divergence is warned, never blocked.',
  resourcePath: 'ejari-registrations',
  fields: [
    {
      key: 'contract_id',
      label: 'Contract',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'tenancy-contracts',
      relationLabelKey: 'contract_number',
      showInGrid: false,
    },
    { key: 'contract_number', label: 'Contract #', type: 'text', showInForm: false, gridWidth: 130 },
    {
      key: 'variance_warnings',
      label: 'Variance warnings',
      type: 'text',
      showInForm: false,
      gridWidth: 260,
      gridValueFormatter: (v) => (Array.isArray(v) ? v.join('; ') : ''),
    },

    { key: 'ejari_contract_number', label: 'Ejari contract #', type: 'text', gridWidth: 150 },
    { key: 'registration_date', label: 'Registration date', type: 'date', gridWidth: 140 },
    { key: 'receipt_number', label: 'Receipt #', type: 'text', showInGrid: false },
    { key: 'total_fees', label: 'Total fees (AED)', type: 'number', showInGrid: false },

    { key: 'start_date', label: 'Start date', type: 'date', gridWidth: 120 },
    { key: 'end_date', label: 'End date', type: 'date', gridWidth: 120 },
    { key: 'grace_start_date', label: 'Grace start date', type: 'date', showInGrid: false },
    { key: 'grace_end_date', label: 'Grace end date', type: 'date', showInGrid: false },

    { key: 'contract_amount', label: 'Contract amount', type: 'number', showInGrid: false },
    { key: 'annual_amount', label: 'Annual amount', type: 'number', showInGrid: false },
    { key: 'actual_contract_amount', label: 'Actual contract amount', type: 'number', showInGrid: false },
    { key: 'actual_annual_amount', label: 'Actual annual amount (AED)', type: 'number', gridWidth: 170 },
    { key: 'discount', label: 'Discount', type: 'number', showInGrid: false },
    { key: 'security_deposit', label: 'Security deposit', type: 'number', showInGrid: false },

    { key: 'owner_number', label: 'Owner number', type: 'text', showInGrid: false },
    { key: 'owner_nationality', label: 'Owner nationality', type: 'text', showInGrid: false },

    { key: 'tenant_name', label: 'Tenant name', type: 'text', showInGrid: false },
    { key: 'tenant_no', label: 'Tenant no', type: 'text', showInGrid: false },
    { key: 'license_number', label: 'Licence number', type: 'text', showInGrid: false },
    { key: 'license_expiry', label: 'Licence expiry', type: 'date', showInGrid: false },
    { key: 'license_issuer', label: 'Licence issuer', type: 'text', showInGrid: false },
    { key: 'tel_no', label: 'Tel no', type: 'text', showInGrid: false },
    { key: 'fax_no', label: 'Fax no', type: 'text', showInGrid: false },

    { key: 'building_name_no', label: 'Building name/no', type: 'text', showInGrid: false },
    { key: 'property_no', label: 'Property no', type: 'text', showInGrid: false },
    { key: 'makani_no', label: 'Makani no', type: 'text', showInGrid: false },
    { key: 'plot_number', label: 'Plot number', type: 'text', showInGrid: false },
    { key: 'land_dm_no', label: 'Land DM no (Affection Plan)', type: 'text', showInGrid: false },
    { key: 'land_area', label: 'Land area', type: 'number', showInGrid: false },
    { key: 'dewa_premise_no', label: 'DEWA premise no', type: 'text', showInGrid: false },

    { key: 'classification_type', label: 'Type', type: 'text', showInGrid: false },
    { key: 'classification_subtype', label: 'SubType', type: 'text', showInGrid: false },
    { key: 'usage', label: 'Usage', type: 'text', showInGrid: false },
    { key: 'size', label: 'Size', type: 'number', showInGrid: false },

    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Active', value: 'active' },
        { label: 'Expired', value: 'expired' },
        { label: 'Superseded', value: 'superseded' },
      ],
      gridWidth: 120,
    },
  ],
};

/** Header fields (plan §3.3 `rental_agreement`). Outbound contract, company -> tenant. */
export const RENTAL_AGREEMENTS_CONFIG: EntityPageConfig = {
  title: 'Rental Agreements',
  subtitle: 'Outbound contract, company → tenant (doc §1.6). No Ejari on this side.',
  resourcePath: 'rental-agreements',
  fields: [
    { key: 'agreement_number', label: 'Agreement number', type: 'text', gridWidth: 160 },
    { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    {
      key: 'term_type',
      label: 'Term type',
      type: 'select',
      options: [
        { label: 'Monthly', value: 'monthly' },
        { label: 'Yearly', value: 'yearly' },
        { label: 'Custom', value: 'custom' },
      ],
    },
    { key: 'start_date', label: 'Start date', type: 'date' },
    { key: 'end_date', label: 'End date', type: 'date' },
    { key: 'annual_rent', label: 'Annual rent (AED)', type: 'number' },
    { key: 'security_deposit_amount', label: 'Security deposit (AED)', type: 'number' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Active', value: 'active' },
        { label: 'Expired', value: 'expired' },
        { label: 'Terminated', value: 'terminated' },
      ],
    },
  ],
};
