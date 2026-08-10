import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Single master for landlords/tenants/suppliers/agents/OTAs (plan §3.2 `counterparty`,
 * doc §2.6) -- one record can hold multiple roles, hence `roles` being free text (comma-
 * separated) rather than a single select. Bank details deliberately excluded from this
 * generic form -- doc §8 flags them as the highest-value fraud target and manager-only
 * to change, which needs real permission checks (deferred, plan §7), not a generic field.
 *
 * `unit_count` is backend-computed (count of units this counterparty co-owns via the
 * `unit_landlord` join table) -- proves the reverse of "one-or-more landlords per unit":
 * a landlord holds one-or-more units. */
export const COUNTERPARTIES_CONFIG: EntityPageConfig = {
  title: 'Landlords & Counterparties',
  subtitle: 'Single master for landlord/tenant/supplier/agent/OTA (doc §2.6). "Units" is a live count of units this landlord co-owns.',
  resourcePath: 'counterparties',
  fields: [
    { key: 'code', label: 'Code', type: 'text', gridWidth: 110 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'unit_count', label: 'Units', type: 'number', showInForm: false, gridWidth: 90 },
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
    { key: 'emirates_id', label: 'Emirates ID', type: 'text' },
    { key: 'hold_flag', label: 'On hold', type: 'boolean', gridWidth: 100 },
  ],
};
