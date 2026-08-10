import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Plan §3.5 `account`. Note: the `Account` SQLAlchemy model and the Appendix A seed
 * data already exist in the backend (Foundation milestone) -- only the `/api/v1/accounts`
 * router itself hasn't been built yet. */
export const CHART_OF_ACCOUNTS_CONFIG: EntityPageConfig = {
  title: 'Chart of Accounts',
  subtitle: 'Appendix A, 108 accounts, already seeded in the backend -- only the API router is still to be built.',
  resourcePath: 'accounts',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 110 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 260 },
    {
      key: 'account_type',
      label: 'Type',
      type: 'select',
      required: true,
      options: [
        { label: 'Asset', value: 'asset' },
        { label: 'Liability', value: 'liability' },
        { label: 'Equity', value: 'equity' },
        { label: 'Revenue', value: 'revenue' },
        { label: 'Cost', value: 'cost' },
        { label: 'Other', value: 'other' },
      ],
    },
    {
      key: 'normal_balance',
      label: 'Normal balance',
      type: 'select',
      required: true,
      options: [
        { label: 'Debit', value: 'debit' },
        { label: 'Credit', value: 'credit' },
      ],
    },
    { key: 'requires_unit', label: 'Requires unit [D]', type: 'boolean', gridWidth: 130 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};

/** Plan §3.5 `journal_entry`. Multi-line journal entry editing (debit/credit lines with
 * dimensions) is a dedicated screen once Accounting-core is built -- this is the header. */
export const JOURNAL_ENTRIES_CONFIG: EntityPageConfig = {
  title: 'Journal Entries',
  subtitle: 'Header record. Multi-line debit/credit entry with dimensions is a dedicated screen once Accounting-core is built.',
  resourcePath: 'journal-entries',
  fields: [
    { key: 'number', label: 'Journal number', type: 'text', gridWidth: 150 },
    { key: 'date', label: 'Date', type: 'date', required: true },
    { key: 'period', label: 'Period', type: 'text', gridWidth: 110 },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Submitted', value: 'submitted' },
        { label: 'Approved', value: 'approved' },
        { label: 'Posted', value: 'posted' },
        { label: 'Reversed', value: 'reversed' },
      ],
    },
    { key: 'source_module', label: 'Source module', type: 'text' },
    { key: 'memo', label: 'Memo', type: 'textarea', showInGrid: false },
  ],
};

/** Plan §3.5 `cheque`. */
export const CHEQUE_LEDGER_CONFIG: EntityPageConfig = {
  title: 'Cheque Ledger',
  subtitle: 'Post-dated cheques (doc §2.1) -- ~50/month. "Held as security" is a distinct status from on-hand payment cheques.',
  resourcePath: 'cheques',
  fields: [
    { key: 'cheque_number', label: 'Cheque number', type: 'text', gridWidth: 150 },
    {
      key: 'direction',
      label: 'Direction',
      type: 'select',
      required: true,
      options: [
        { label: 'Received', value: 'received' },
        { label: 'Issued', value: 'issued' },
      ],
    },
    { key: 'counterparty_id', label: 'Counterparty ID', type: 'text', required: true },
    { key: 'payee_name', label: 'Payee (as written)', type: 'text' },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true },
    { key: 'cheque_date', label: 'Cheque date', type: 'date' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'On hand', value: 'on_hand' },
        { label: 'Deposited', value: 'deposited' },
        { label: 'Presented', value: 'presented' },
        { label: 'Cleared', value: 'cleared' },
        { label: 'Bounced', value: 'bounced' },
        { label: 'Replaced', value: 'replaced' },
        { label: 'Returned', value: 'returned' },
        { label: 'Cancelled', value: 'cancelled' },
        { label: 'Held as security', value: 'held_as_security' },
      ],
    },
  ],
};

/** Plan §3.5 `cash_transaction`. */
export const CASH_LEDGER_CONFIG: EntityPageConfig = {
  title: 'Cash Ledger',
  subtitle: 'Petty cash and cash collections by location/custodian (doc §2.2).',
  resourcePath: 'cash-transactions',
  fields: [
    { key: 'date', label: 'Date', type: 'date', required: true },
    { key: 'custodian_user_id', label: 'Custodian', type: 'text' },
    { key: 'location', label: 'Location', type: 'text' },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true },
    { key: 'category', label: 'Category', type: 'text' },
    { key: 'counterparty_id', label: 'Counterparty ID', type: 'text' },
    { key: 'reference', label: 'Reference', type: 'text' },
  ],
};

/** Plan §3.5 `invoice`. Same object for sales + purchase per doc §2.9. */
export const INVOICES_CONFIG: EntityPageConfig = {
  title: 'Invoices',
  subtitle: 'Sales (to guests/tenants/landlords) and purchase invoices share one object (doc §2.9).',
  resourcePath: 'invoices',
  fields: [
    { key: 'invoice_number', label: 'Invoice number', type: 'text', gridWidth: 150 },
    {
      key: 'direction',
      label: 'Direction',
      type: 'select',
      required: true,
      options: [
        { label: 'Sales', value: 'sales' },
        { label: 'Purchase', value: 'purchase' },
      ],
    },
    { key: 'counterparty_id', label: 'Counterparty ID', type: 'text', required: true },
    { key: 'date', label: 'Date', type: 'date' },
    { key: 'due_date', label: 'Due date', type: 'date' },
    { key: 'total_amount', label: 'Total (AED)', type: 'number' },
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
        { label: 'Part paid', value: 'part_paid' },
        { label: 'Cancelled', value: 'cancelled' },
      ],
    },
  ],
};
