import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Plan §3.5 `bill`. */
export const BILLS_CONFIG: EntityPageConfig = {
  title: 'Bills',
  subtitle: 'Supplier and operating costs (doc Section 6). No approval workflow in v1 (confirmed dropped).',
  resourcePath: 'bills',
  fields: [
    { key: 'bill_number', label: 'Bill number', type: 'text', gridWidth: 150 },
    { key: 'supplier_counterparty_id', label: 'Supplier ID', type: 'text', required: true },
    { key: 'unit_id', label: 'Unit ID', type: 'text' },
    { key: 'bill_date', label: 'Bill date', type: 'date' },
    { key: 'due_date', label: 'Due date', type: 'date' },
    { key: 'amount', label: 'Amount (AED)', type: 'number', required: true },
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
    },
  ],
};

/** Plan §3.5 `bill_recurring_template`. */
export const BILL_RECURRING_TEMPLATES_CONFIG: EntityPageConfig = {
  title: 'Recurring Templates',
  subtitle: 'Almost every bill recurs monthly (doc §6.1) -- generates expected bills and feeds the missing-bill report.',
  resourcePath: 'bill-recurring-templates',
  fields: [
    { key: 'supplier_counterparty_id', label: 'Supplier ID', type: 'text', required: true },
    { key: 'unit_id', label: 'Unit ID', type: 'text' },
    { key: 'cost_type_id', label: 'Cost type ID', type: 'text' },
    { key: 'expected_amount', label: 'Expected amount (AED)', type: 'number' },
    { key: 'expected_day_of_month', label: 'Expected day of month', type: 'number', gridWidth: 170 },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
  ],
};
