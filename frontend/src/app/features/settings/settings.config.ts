import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Settings > Currencies -- multi-currency support. Manually-maintained list picked
 * from everywhere a "currency" field used to be free text (Bank Accounts, Bank
 * Statement, Company's base currency). `code` is a manually-entered, unique 3-digit
 * identifier; `name` is the short code shown everywhere else (e.g. "AED"). */
export const CURRENCIES_CONFIG: EntityPageConfig = {
  title: 'Currencies',
  subtitle: 'Multi-currency support -- picked from here everywhere a currency field appears.',
  resourcePath: 'currencies',
  auditEntityType: 'currency',
  fields: [
    { key: 'code', label: 'Unique code', type: 'text', required: true, gridWidth: 120 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 140 },
    { key: 'full_name', label: 'Full name', type: 'text', required: true, gridWidth: 240 },
    {
      key: 'rate_to_base',
      label: 'Rate to base currency',
      type: 'number',
      gridWidth: 170,
      gridValueFormatter: (v) => (v === null || v === undefined ? 'Not set' : String(v)),
    },
  ],
};

/** Settings > Bank Account Columns -- the designer behind BOTH Accounting > Bank
 * Statement - Original and Bank Statement - Reconciliation. Each bank account
 * defines its own fully custom column set per view (banks export statements in
 * different shapes) -- add one row here per column that account's grid should
 * show, tagged with which of the two views it belongs to. `key` is the machine
 * name the value is stored under; `sort_order` controls left-to-right column order
 * within that view.
 *
 * No `relationCreateFields` on `bank_account_id` -- pulling in Bank Accounts' own
 * field list here would create a circular import (accounting.config.ts already
 * imports Currencies from this file). Create the bank account first under
 * Accounting > Bank Accounts, then configure its columns here. */
export const BANK_ACCOUNT_COLUMNS_CONFIG: EntityPageConfig = {
  title: 'Bank Account Columns',
  subtitle: 'Custom columns per bank account -- picked up by both Bank Statement - Original and - Reconciliation.',
  resourcePath: 'bank-account-columns',
  auditEntityType: 'bank_account_column',
  fields: [
    {
      key: 'bank_account_id',
      label: 'Bank account',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'bank-accounts',
      relationLabelKey: 'account_name',
      showInGrid: false,
    },
    { key: 'bank_account_label', label: 'Bank account', type: 'text', showInForm: false, gridWidth: 180 },
    {
      key: 'applies_to',
      label: 'View',
      type: 'select',
      required: true,
      options: [
        { label: 'Bank Statement - Original', value: 'original' },
        { label: 'Bank Statement - Reconciliation', value: 'reconciliation' },
      ],
      gridWidth: 220,
    },
    { key: 'key', label: 'Column key', type: 'text', required: true, gridWidth: 160 },
    { key: 'label', label: 'Column label', type: 'text', required: true, gridWidth: 180 },
    {
      key: 'data_type',
      label: 'Data type',
      type: 'select',
      required: true,
      options: [
        { label: 'Text', value: 'text' },
        { label: 'Number', value: 'number' },
        { label: 'Date', value: 'date' },
      ],
      gridWidth: 120,
    },
    { key: 'sort_order', label: 'Sort order', type: 'number', gridWidth: 120 },
    {
      key: 'semantic_role',
      label: 'Role (for matching)',
      type: 'select',
      options: [
        { label: 'Amount', value: 'amount' },
        { label: 'Date', value: 'date' },
        { label: 'Reference', value: 'reference' },
      ],
      gridWidth: 160,
    },
  ],
};

/** Plan §3.1 `document_sequence` (doc §5.4). */
export const NUMBERING_CONFIG: EntityPageConfig = {
  title: 'Numbering',
  subtitle: 'Configurable sequential numbering per document type (doc §5.4). Backend already has NumberingService; this exposes it for configuration.',
  resourcePath: 'document-sequences',
  fields: [
    { key: 'doc_type', label: 'Document type', type: 'text', required: true, gridWidth: 180 },
    { key: 'prefix', label: 'Prefix', type: 'text', gridWidth: 120 },
    { key: 'next_number', label: 'Next number', type: 'number', gridWidth: 130 },
    {
      key: 'reset_cycle',
      label: 'Reset cycle',
      type: 'select',
      required: true,
      options: [
        { label: 'Never', value: 'never' },
        { label: 'Yearly', value: 'yearly' },
      ],
    },
  ],
};

/** Plan §3.5 `tax_code` (doc §5.7). */
export const TAX_CODES_CONFIG: EntityPageConfig = {
  title: 'Tax Codes',
  subtitle: 'Central VAT configuration (doc §5.7) -- rate, treatment, effective dates. Never hard-coded 5%.',
  resourcePath: 'tax-codes',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 130 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 200 },
    { key: 'rate', label: 'Rate (%)', type: 'number', gridWidth: 110 },
    {
      key: 'treatment',
      label: 'Treatment',
      type: 'select',
      required: true,
      options: [
        { label: 'Standard', value: 'standard' },
        { label: 'Exempt', value: 'exempt' },
        { label: 'Zero-rated', value: 'zero' },
        { label: 'Reverse charge', value: 'reverse_charge' },
      ],
    },
    { key: 'effective_from', label: 'Effective from', type: 'date' },
    { key: 'effective_to', label: 'Effective to', type: 'date' },
  ],
};

/** Plan §3.5 `setup_cost_type` (doc §7.2 designer). */
export const SETUP_COST_TYPES_CONFIG: EntityPageConfig = {
  title: 'Setup Cost Types',
  subtitle: 'The designer for unit setup cost categories (doc §7.2) -- e.g. DEWA deposit, agency fee, DTCM permit fee.',
  resourcePath: 'setup-cost-types',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 140 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    {
      key: 'default_treatment',
      label: 'Default treatment',
      type: 'select',
      required: true,
      options: [
        { label: 'Refundable deposit', value: 'refundable_deposit' },
        { label: 'Expense', value: 'expense' },
        { label: 'Capitalise - prepaid', value: 'capitalise_prepaid' },
        { label: 'Capitalise - fixed asset', value: 'capitalise_fixed_asset' },
      ],
    },
    { key: 'refundable', label: 'Refundable', type: 'boolean', gridWidth: 110 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};

/** Plan §3.5 `cost_type` (doc §7.8, two-level type/subtype tree -- kept flat here). */
export const COST_TYPES_CONFIG: EntityPageConfig = {
  title: 'Cost Types',
  subtitle: 'Direct-cost / overhead category tree (doc §7.8), e.g. DEWA → electricity. Kept flat for now; hierarchy display comes with the full module.',
  resourcePath: 'cost-types',
  fields: [
    { key: 'type', label: 'Type', type: 'text', required: true, gridWidth: 180 },
    { key: 'subtype', label: 'Subtype', type: 'text', gridWidth: 180 },
    {
      key: 'direct_or_overhead',
      label: 'Direct or overhead',
      type: 'select',
      required: true,
      options: [
        { label: 'Direct', value: 'direct' },
        { label: 'Overhead', value: 'overhead' },
      ],
    },
    { key: 'recurring', label: 'Recurring', type: 'boolean', gridWidth: 110 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};

/** Plan §3.5 `asset_category` (doc §7.5). */
export const ASSET_CATEGORIES_CONFIG: EntityPageConfig = {
  title: 'Asset Categories',
  subtitle: 'Depreciation policy by category (doc §7.5). v1 posting logic implements straight-line only; other methods are configurable but unused.',
  resourcePath: 'asset-categories',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 130 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 200 },
    { key: 'useful_life_months', label: 'Useful life (months)', type: 'number', gridWidth: 160 },
    {
      key: 'method',
      label: 'Method',
      type: 'select',
      required: true,
      options: [
        { label: 'Linear (straight-line)', value: 'linear' },
        { label: 'Reducing balance', value: 'reducing_balance' },
        { label: 'Sum-of-years-digits', value: 'sum_of_years' },
        { label: 'Custom', value: 'custom' },
      ],
    },
    { key: 'residual_pct', label: 'Residual %', type: 'number', gridWidth: 110 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};

/** Plan §3.1 `reference_list_item` (doc §7.4) -- the generic list designer covering
 * unit_type, block_type, utility_type, task_type, and every other "list maintained by
 * you". `list_name` is itself an editable field so any list can be extended here. */
export const REFERENCE_LISTS_CONFIG: EntityPageConfig = {
  title: 'Reference Lists',
  subtitle: 'Every list maintained by you (doc §7.4): unit types, block types, utility types, task types, and more -- never hard-coded.',
  resourcePath: 'reference-lists',
  fields: [
    { key: 'list_name', label: 'List', type: 'text', required: true, gridWidth: 160 },
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 160 },
    { key: 'label', label: 'Label', type: 'text', required: true, gridWidth: 220 },
    { key: 'is_available', label: 'Counts as available?', type: 'boolean', gridWidth: 170 },
    { key: 'sort_order', label: 'Sort order', type: 'number', gridWidth: 110 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};
