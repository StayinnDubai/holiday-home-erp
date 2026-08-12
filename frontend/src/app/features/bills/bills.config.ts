import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { formatAmount } from '../../shared/utils/amount';
import { COUNTERPARTIES_CONFIG } from '../counterparties/counterparties.config';
import { TAX_CODES_CONFIG } from '../settings/settings.config';

/** Plan §3.5 `bill` (doc §6, accounts payable). Reaching `status: 'recorded'` posts
 * the liability (backend/app/posting_rules/bill.py, Dr `contra_account_id` / Cr
 * "2010 Trade payables - suppliers"), plus any VAT line(s) its tax code calls for
 * (posting_rules/tax.py); reaching `status: 'paid'` clears it against
 * `bank_account_id` -- mirrors Cheque's two-stage posting exactly. `tax_amount` is
 * entered manually (e.g. amount * tax code's rate), not server-computed, matching
 * every other numeric field in this codebase. */
export const BILLS_CONFIG: EntityPageConfig = {
  title: 'Bills',
  subtitle: 'Supplier and operating costs (doc Section 6). No approval workflow in v1 (confirmed dropped).',
  resourcePath: 'bills',
  auditEntityType: 'bill',
  fields: [
    { key: 'bill_number', label: 'Bill number', type: 'text', gridWidth: 150, showInForm: false },
    {
      key: 'supplier_counterparty_id',
      label: 'Supplier',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'supplier_name', label: 'Supplier', type: 'text', showInForm: false, gridWidth: 200 },
    {
      key: 'unit_id',
      label: 'Unit',
      type: 'relation-select',
      relationResourcePath: 'units',
      relationLabelKey: 'unit_code',
      showInGrid: false,
    },
    { key: 'unit_code', label: 'Unit', type: 'text', showInForm: false, gridWidth: 110 },
    { key: 'bill_date', label: 'Bill date', type: 'date', gridWidth: 120 },
    { key: 'due_date', label: 'Due date', type: 'date', gridWidth: 120 },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true, gridWidth: 130, gridValueFormatter: formatAmount },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Recorded', value: 'recorded' },
        { label: 'Scheduled', value: 'scheduled' },
        { label: 'Paid', value: 'paid' },
        { label: 'Disputed', value: 'disputed' },
        { label: 'Cancelled', value: 'cancelled' },
      ],
      gridWidth: 130,
    },
    {
      key: 'contra_account_id',
      label: 'Expense account',
      type: 'relation-select',
      relationResourcePath: 'accounts',
      relationLabelKey: 'code',
      showInGrid: false,
    },
    { key: 'contra_account_code', label: 'Expense account', type: 'text', showInForm: false, gridWidth: 130 },
    {
      key: 'bank_account_id',
      label: 'Paid from (bank account)',
      type: 'relation-select',
      relationResourcePath: 'bank-accounts',
      relationLabelKey: 'account_name',
      showInGrid: false,
    },
    { key: 'bank_account_label', label: 'Paid from', type: 'text', showInForm: false, gridWidth: 180 },
    {
      key: 'tax_code_id',
      label: 'Tax code',
      type: 'relation-select',
      relationResourcePath: 'tax-codes',
      relationLabelKey: 'name',
      relationCreateFields: TAX_CODES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'tax_code_label', label: 'Tax code', type: 'text', showInForm: false, gridWidth: 140 },
    { key: 'tax_amount', label: 'Tax amount (AED)', type: 'number', gridWidth: 130, gridValueFormatter: formatAmount },
    {
      key: 'tenancy_contract_id',
      label: 'Tenancy contract',
      type: 'relation-select',
      relationResourcePath: 'tenancy-contracts',
      relationLabelKey: 'contract_number',
      showInGrid: false,
    },
    { key: 'tenancy_contract_number', label: 'Tenancy contract', type: 'text', showInForm: false, gridWidth: 140 },
    {
      key: 'bill_document',
      label: 'Bill document',
      type: 'attachments',
      attachmentEntityType: 'bill',
      showInGrid: false,
    },
  ],
};

/** Plan §3.5 `bill_recurring_template`. Not built yet -- recurring generation needs
 * a scheduler, out of scope alongside Bills itself; kept as a placeholder route. */
export const BILL_RECURRING_TEMPLATES_CONFIG: EntityPageConfig = {
  title: 'Recurring Templates',
  subtitle: 'Almost every bill recurs monthly (doc §6.1) -- generates expected bills and feeds the missing-bill report.',
  resourcePath: 'bill-recurring-templates',
  fields: [
    { key: 'supplier_counterparty_id', label: 'Supplier ID', type: 'text', required: true },
    { key: 'unit_id', label: 'Unit ID', type: 'text' },
    { key: 'cost_type_id', label: 'Cost type ID', type: 'text' },
    { key: 'expected_amount', label: 'Expected amount (AED)', type: 'number', gridValueFormatter: formatAmount },
    { key: 'expected_day_of_month', label: 'Expected day of month', type: 'number', gridWidth: 170 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};
