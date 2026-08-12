import { EntityFieldConfig, EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { COUNTERPARTY_GROUPS_CONFIG } from './counterparty-groups.config';

/** Single master for landlords/tenants/suppliers/agents/OTAs (plan §3.2 `counterparty`,
 * doc §2.6) -- one record can hold multiple roles, hence `roles` being free text (comma-
 * separated) rather than a single select. Bank details deliberately excluded from this
 * generic form -- doc §8 flags them as the highest-value fraud target and manager-only
 * to change, which needs real permission checks (deferred, plan §7), not a generic field.
 *
 * Shared by two pages: General > Landlords (`landlords.config.ts`, filtered to
 * counterparties in an "is landlord group" group, adds the `unit_count` column) and
 * Accounting > Counterparties (this file, unfiltered, no unit column -- a counterparty
 * need not be attached to any specific unit). */
export const COUNTERPARTY_BASE_FIELDS: EntityFieldConfig[] = [
  { key: 'code', label: 'Code', type: 'text', gridWidth: 110 },
  { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
  {
    key: 'type',
    label: 'Type',
    type: 'select',
    required: true,
    options: [
      { label: 'Individual', value: 'individual' },
      { label: 'Company', value: 'company' },
    ],
  },
  { key: 'roles', label: 'Roles (comma-separated)', type: 'text', gridWidth: 220 },
  { key: 'trn', label: 'TRN', type: 'text' },
  { key: 'nationality', label: 'Nationality', type: 'text', showInGrid: false },
  { key: 'emirates_id', label: 'Emirates ID', type: 'text' },
  { key: 'emirates_id_issue_date', label: 'Emirates ID issue date', type: 'date', showInGrid: false },
  { key: 'emirates_id_expiry_date', label: 'Emirates ID expiry date', type: 'date', gridWidth: 150 },
  { key: 'passport_number', label: 'Passport number', type: 'text', showInGrid: false },
  { key: 'passport_issue_date', label: 'Passport issue date', type: 'date', showInGrid: false },
  { key: 'passport_expiry_date', label: 'Passport expiry date', type: 'date', showInGrid: false },
  { key: 'hold_flag', label: 'On hold', type: 'boolean', gridWidth: 100 },
  {
    key: 'id_documents',
    label: 'ID documents (passport, Emirates ID scans, etc.)',
    type: 'attachments-list',
    attachmentEntityType: 'counterparty_document',
    showInGrid: false,
  },
  {
    key: 'group_id',
    label: 'Counterparty group',
    type: 'relation-select',
    relationResourcePath: 'counterparty-groups',
    relationLabelKey: 'name',
    relationCreateFields: COUNTERPARTY_GROUPS_CONFIG.fields,
    showInGrid: false,
  },
  { key: 'group_name', label: 'Group', type: 'text', showInForm: false, gridWidth: 160 },
];

export const COUNTERPARTIES_CONFIG: EntityPageConfig = {
  title: 'Counterparties',
  subtitle: 'Single master for landlord/tenant/supplier/agent/OTA (doc §2.6). All counterparties, regardless of group.',
  resourcePath: 'counterparties',
  auditEntityType: 'counterparty',
  // Unlike Landlords (landlords.config.ts), this grid/form drops "Roles" -- not
  // useful once the list isn't already scoped to one role (landlord).
  fields: COUNTERPARTY_BASE_FIELDS.filter((f) => f.key !== 'roles'),
};
