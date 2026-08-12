import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { COUNTERPARTY_BASE_FIELDS } from './counterparties.config';

/** General > Landlords -- same underlying `counterparty` resource as Accounting >
 * Counterparties (`counterparties.config.ts`), filtered server-side (`landlord_only`)
 * to counterparties whose group is flagged "Landlord group" (`is_landlord_group` on
 * `CounterpartyGroup`). Adds `unit_count` (backend-computed count of units this
 * landlord co-owns via the `unit_landlord` join table) -- proves the reverse of
 * "one-or-more landlords per unit": a landlord holds one-or-more units. Accounting's
 * Counterparties grid omits this column since a counterparty there need not be
 * attached to any specific unit. */
export const LANDLORDS_CONFIG: EntityPageConfig = {
  title: 'Landlords',
  subtitle: 'Counterparties belonging to a landlord group. "Units" is a live count of units this landlord co-owns.',
  resourcePath: 'counterparties',
  auditEntityType: 'counterparty',
  extraListParams: { landlord_only: 'true' },
  fields: [
    COUNTERPARTY_BASE_FIELDS[0],
    COUNTERPARTY_BASE_FIELDS[1],
    { key: 'unit_count', label: 'Units', type: 'number', showInForm: false, gridWidth: 90 },
    ...COUNTERPARTY_BASE_FIELDS.slice(2),
  ],
};
