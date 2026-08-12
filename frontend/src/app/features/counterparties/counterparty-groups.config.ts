import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Accounting > Counterparty Group -- a manually-maintained classification for
 * counterparties (e.g. "Landlords - Downtown", "OTA channels", "Utility suppliers").
 * `counterparty_count` is backend-computed (count of counterparties currently
 * assigned to this group), same pattern as Buildings' `unit_count`. Purely
 * organisational -- no commercial terms live here (same principle doc §1.2 already
 * applies to the landlord record itself). */
export const COUNTERPARTY_GROUPS_CONFIG: EntityPageConfig = {
  title: 'Counterparty Group',
  subtitle: 'Manually-maintained groups for landlords/tenants/suppliers/agents/OTAs. "Counterparties" is a live count of members.',
  resourcePath: 'counterparty-groups',
  auditEntityType: 'counterparty_group',
  fields: [
    { key: 'code', label: 'Code', type: 'text', required: true, gridWidth: 120 },
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'counterparty_count', label: 'Counterparties', type: 'number', showInForm: false, gridWidth: 140 },
    { key: 'notes', label: 'Notes', type: 'textarea', showInGrid: false },
    { key: 'active', label: 'Active', type: 'boolean', gridWidth: 100 },
    {
      key: 'is_landlord_group',
      label: 'Landlord group',
      type: 'boolean',
      gridWidth: 130,
    },
  ],
};
