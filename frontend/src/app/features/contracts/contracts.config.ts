import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Header fields (plan §3.3 `tenancy_contract`). Ejari registration, POA, and the
 * payment schedule/cheque generation are separate tabs/workflows once this module's
 * backend milestone is built -- not folded into this generic form. */
export const TENANCY_CONTRACTS_CONFIG: EntityPageConfig = {
  title: 'Tenancy Contracts',
  subtitle: 'Inbound lease, company ← landlord (doc §1.4). Ejari and POA are separate tabs once this milestone is built.',
  resourcePath: 'tenancy-contracts',
  fields: [
    { key: 'contract_number', label: 'Contract number', type: 'text', gridWidth: 160 },
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    {
      key: 'contract_type',
      label: 'Type',
      type: 'select',
      options: [
        { label: 'New', value: 'new' },
        { label: 'Renewal', value: 'renewal' },
      ],
    },
    { key: 'start_date', label: 'Start date', type: 'date' },
    { key: 'end_date', label: 'End date', type: 'date' },
    { key: 'total_annual_rent', label: 'Annual rent (AED)', type: 'number' },
    { key: 'instalment_count', label: 'Instalments', type: 'number', gridWidth: 110 },
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
