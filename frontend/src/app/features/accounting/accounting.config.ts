import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { formatAmount } from '../../shared/utils/amount';
import { COUNTERPARTIES_CONFIG } from '../counterparties/counterparties.config';
import { CURRENCIES_CONFIG } from '../settings/settings.config';

/** Plan §3.5 `account` / doc §2.0, Appendix A. All 108 accounts are seeded in the
 * backend (app/seed/chart_of_accounts.py, transcribed verbatim from Appendix A);
 * this page is the CRUD layer on top of that seed -- for adding an account Appendix
 * A didn't anticipate, or renaming one before it's used in a posting. `[D]` marks
 * accounts that require a unit dimension on every posting; `[F]` marks Model B
 * accounts, unused until Phase 8. `parent_account_id` supports the doc's
 * "multi-level" chart (doc §2.0), e.g. rolling DEWA sub-accounts under a parent. */
export const CHART_OF_ACCOUNTS_CONFIG: EntityPageConfig = {
  title: 'Chart of Accounts',
  subtitle: 'Appendix A, 108 accounts (doc §2.0) -- four-digit, grouped by type, with room to insert.',
  resourcePath: 'accounts',
  auditEntityType: 'account',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 100 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 300 },
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
      gridWidth: 110,
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
      gridWidth: 130,
    },
    {
      key: 'parent_account_id',
      label: 'Parent account',
      type: 'relation-select',
      relationResourcePath: 'accounts',
      relationLabelKey: 'code',
      showInGrid: false,
    },
    { key: 'parent_account_code', label: 'Parent', type: 'text', showInForm: false, gridWidth: 100 },
    { key: 'requires_unit', label: 'Requires unit [D]', type: 'boolean', gridWidth: 130 },
    { key: 'is_model_b_only', label: 'Model B only [F]', type: 'boolean', gridWidth: 130 },
    { key: 'control_account', label: 'Control account', type: 'boolean', gridWidth: 130 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 90 },
  ],
};

/** Plan §3.5 `journal_entry`. Only `status: 'posted'` entries count toward account
 * balances / Financial Reports (backend/app/services/reports.py) -- draft/submitted/
 * approved are visible but inert. Once posted, an entry (including its lines) is
 * immutable server-side -- corrections are a new reversing entry, not an edit.
 * `number`/`period` are server-generated (NumberingService / derived from `date`),
 * `source_module` defaults to 'manual' for anything created here -- 'cheque' entries
 * come from posting_rules/cheque.py instead, not this form. */
export const JOURNAL_ENTRIES_CONFIG: EntityPageConfig = {
  title: 'Journal Entries',
  subtitle: 'General ledger. Draft/submitted/approved entries are inert -- only posted entries move a balance.',
  resourcePath: 'journal-entries',
  auditEntityType: 'journal_entry',
  fields: [
    { key: 'number', label: 'Journal number', type: 'text', gridWidth: 150, showInForm: false },
    { key: 'date', label: 'Date', type: 'date', required: true },
    { key: 'period', label: 'Period', type: 'text', gridWidth: 110, showInForm: false },
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
    { key: 'source_module', label: 'Source module', type: 'text', showInForm: false },
    { key: 'memo', label: 'Memo', type: 'textarea', showInGrid: false },
    { key: 'lines', label: 'Lines', type: 'journal-entry-lines', showInGrid: false },
  ],
};

/** Plan §3.5 `cheque` (doc §2.1) -- post-dated cheques, ~50/month. "Held as security"
 * is a distinct status from on-hand payment cheques.
 *
 * `actual_drawdown_date` is the date the cheque genuinely cleared, distinct from
 * `cheque_date` (the date written on it). It can be set two ways -- typed manually,
 * or (for now, as a placeholder) via a "Reconcile from bank statement" button that
 * opens the same date picker -- and `drawdown_source` records which, via the
 * 'action-date' field type (shared/crud/entity-form.component.ts). Real matching
 * against imported bank statement lines is a later milestone.
 *
 * `cheque_image` reuses the generic attachments endpoint (doc §5.3) to let a photo
 * of the physical cheque be attached once the cheque record has been saved. */
export const CHEQUE_LEDGER_CONFIG: EntityPageConfig = {
  title: 'Cheque Ledger',
  subtitle: 'Post-dated cheques (doc §2.1) -- ~50/month. "Held as security" is a distinct status from on-hand payment cheques.',
  resourcePath: 'cheques',
  auditEntityType: 'cheque',
  fields: [
    { key: 'cheque_number', label: 'Cheque number', type: 'text', required: true, gridWidth: 150 },
    {
      key: 'direction',
      label: 'Direction',
      type: 'select',
      required: true,
      options: [
        { label: 'Received', value: 'received' },
        { label: 'Issued', value: 'issued' },
      ],
      gridWidth: 110,
    },
    {
      key: 'counterparty_id',
      label: 'Counterparty',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'counterparty_name', label: 'Counterparty', type: 'text', showInForm: false, gridWidth: 180 },
    { key: 'payee_name', label: 'Payee (as written)', type: 'text', gridWidth: 180 },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true, gridWidth: 130, gridValueFormatter: formatAmount },
    { key: 'cheque_date', label: 'Cheque date', type: 'date', gridWidth: 120 },
    {
      key: 'actual_drawdown_date',
      label: 'Actual drawdown date',
      type: 'action-date',
      sourceFieldKey: 'drawdown_source',
      gridWidth: 170,
    },
    {
      key: 'drawdown_source',
      label: 'Drawdown source',
      type: 'text',
      showInForm: false,
      gridWidth: 170,
      gridValueFormatter: (v) => (v === 'manual' ? 'Manual' : v === 'bank_reconciliation' ? 'Bank reconciliation' : ''),
    },
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
      gridWidth: 140,
    },
    {
      key: 'contra_account_id',
      label: 'Settles (GL account)',
      type: 'relation-select',
      relationResourcePath: 'accounts',
      relationLabelKey: 'code',
      showInGrid: false,
    },
    { key: 'contra_account_code', label: 'Settles', type: 'text', showInForm: false, gridWidth: 110 },
    {
      key: 'bank_account_id',
      label: 'Clears through (bank account)',
      type: 'relation-select',
      relationResourcePath: 'bank-accounts',
      relationLabelKey: 'account_name',
      showInGrid: false,
    },
    { key: 'bank_account_label', label: 'Clears through', type: 'text', showInForm: false, gridWidth: 180 },
    {
      key: 'cheque_image',
      label: 'Cheque image',
      type: 'attachments',
      attachmentEntityType: 'cheque',
      showInGrid: false,
    },
  ],
};

/** Accounting > Bank Accounts -- the company's own bank accounts. Distinct from a
 * `Counterparty` of role "Bank" (the signatory relationship) -- this is the account
 * itself, one row per account held at that bank. `code` is a manually-entered,
 * unique 3-digit identifier (no auto-numbering rule given, unlike e.g. unit_code). */
export const BANK_ACCOUNTS_CONFIG: EntityPageConfig = {
  title: 'Bank Accounts',
  subtitle: "The company's own bank accounts. Unique code is entered manually (3 digits).",
  resourcePath: 'bank-accounts',
  auditEntityType: 'bank_account',
  fields: [
    { key: 'code', label: 'Unique code', type: 'text', required: true, gridWidth: 110 },
    {
      key: 'bank_id',
      label: 'Bank name',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'counterparties',
      relationLabelKey: 'name',
      relationCreateFields: COUNTERPARTIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'bank_name', label: 'Bank name', type: 'text', showInForm: false, gridWidth: 180 },
    { key: 'account_name', label: 'Account name', type: 'text', required: true, gridWidth: 200 },
    { key: 'account_type', label: 'Account type', type: 'text', gridWidth: 140 },
    { key: 'account_iban', label: 'Account IBAN', type: 'text', gridWidth: 220 },
    { key: 'account_number', label: 'Account number', type: 'text', gridWidth: 170 },
    {
      key: 'currency_id',
      label: 'Account currency',
      type: 'relation-select',
      relationResourcePath: 'currencies',
      relationLabelKey: 'name',
      relationCreateFields: CURRENCIES_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'currency_name', label: 'Account currency', type: 'text', showInForm: false, gridWidth: 140 },
    {
      key: 'status',
      label: 'Account status',
      type: 'select',
      required: true,
      options: [
        { label: 'Active', value: 'active' },
        { label: 'Closed', value: 'closed' },
        { label: 'Freezed', value: 'freezed' },
      ],
      gridWidth: 130,
    },
    { key: 'open_date', label: 'Account open date', type: 'date', gridWidth: 150 },
    { key: 'close_date', label: 'Account close date', type: 'date', gridWidth: 150 },
    {
      key: 'chart_account_id',
      label: 'Chart of account code',
      type: 'relation-select',
      relationResourcePath: 'accounts',
      relationLabelKey: 'code',
      showInGrid: false,
    },
    { key: 'chart_account_code', label: 'Chart of account code', type: 'text', showInForm: false, gridWidth: 170 },
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
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true, gridValueFormatter: formatAmount },
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
    { key: 'total_amount', label: 'Total (AED)', type: 'number', gridValueFormatter: formatAmount },
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

