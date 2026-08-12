import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { formatAmount } from '../../shared/utils/amount';

/** Plan §3.3 `dtcm_permit`. */
export const DTCM_PERMITS_CONFIG: EntityPageConfig = {
  title: 'DTCM Permits',
  subtitle: 'The licence that makes a unit legal as a holiday home (doc §1.8).',
  resourcePath: 'dtcm-permits',
  fields: [
    { key: 'permit_number', label: 'Permit number', type: 'text', gridWidth: 160 },
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    { key: 'issue_date', label: 'Issue date', type: 'date' },
    { key: 'expiry_date', label: 'Expiry date', type: 'date' },
    { key: 'fee', label: 'Fee (AED)', type: 'number', gridValueFormatter: formatAmount },
    { key: 'bedrooms_permitted', label: 'Bedrooms permitted', type: 'number', gridWidth: 150 },
    { key: 'max_guests', label: 'Max guests', type: 'number', gridWidth: 120 },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Active', value: 'active' },
        { label: 'Expired', value: 'expired' },
        { label: 'Cancelled', value: 'cancelled' },
      ],
    },
  ],
};

/** Plan §3.3 `move_in_permit`. */
export const MOVE_IN_PERMITS_CONFIG: EntityPageConfig = {
  title: 'Move-in Permits',
  subtitle: 'Building/community management approval (doc §1.7) -- no cost, 1-2 day turnaround.',
  resourcePath: 'move-in-permits',
  fields: [
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    { key: 'building_id', label: 'Building ID', type: 'text' },
    { key: 'permit_type', label: 'Permit / trigger type', type: 'text' },
    { key: 'move_date', label: 'Move date', type: 'date' },
    { key: 'applied_date', label: 'Applied date', type: 'date' },
    { key: 'issue_date', label: 'Issue date', type: 'date' },
    { key: 'reference_number', label: 'Reference number', type: 'text' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Applied', value: 'applied' },
        { label: 'Issued', value: 'issued' },
        { label: 'Cancelled', value: 'cancelled' },
      ],
    },
  ],
};
