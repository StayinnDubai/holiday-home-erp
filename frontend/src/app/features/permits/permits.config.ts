import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { formatAmount } from '../../shared/utils/amount';
import { UNITS_CONFIG } from '../units/units.config';

/** DTCM Permits (doc §1.8) -- the licence that makes a unit legal as a holiday
 * home. Fields transcribed verbatim from a real DTCM Unit Permit certificate, same
 * design principle as Ejari Registrations (contracts.config.ts): stored as printed
 * even where a value could instead be looked up from Unit/Building, since
 * divergence from those records is itself information. `contract_id` is the
 * tenancy contract in effect when the permit was issued/renewed. */
export const DTCM_PERMITS_CONFIG: EntityPageConfig = {
  title: 'DTCM Permits',
  subtitle: 'The licence that makes a unit legal as a holiday home (doc §1.8) -- transcribed verbatim from the certificate.',
  resourcePath: 'dtcm-permits',
  auditEntityType: 'dtcm_permit',
  fields: [
    { key: 'permit_number', label: 'Permit number', type: 'text', required: true, gridWidth: 170 },
    {
      key: 'unit_id',
      label: 'Unit',
      type: 'relation-select',
      required: true,
      relationResourcePath: 'units',
      relationLabelKey: 'unit_name',
      relationCreateFields: UNITS_CONFIG.fields,
      showInGrid: false,
    },
    { key: 'unit_code', label: 'Unit', type: 'text', showInForm: false, gridWidth: 100 },
    {
      key: 'contract_id',
      label: 'Tenancy contract',
      type: 'relation-select',
      relationResourcePath: 'tenancy-contracts',
      relationLabelKey: 'contract_number',
      showInGrid: false,
    },
    { key: 'contract_number', label: 'Contract #', type: 'text', showInForm: false, gridWidth: 130 },

    { key: 'dtcm_unit_unique_code', label: 'DTCM unit unique code', type: 'text', gridWidth: 170 },
    { key: 'operator_name', label: 'Operator name', type: 'text', showInGrid: false },
    { key: 'operator_license_number', label: 'Operator licence number', type: 'text', showInGrid: false },
    { key: 'operator_license_expiry_date', label: 'Operator licence expiry', type: 'date', gridWidth: 170 },
    { key: 'operator_location', label: 'Operator location', type: 'text', showInGrid: false },
    { key: 'operator_contact_details', label: 'Operator contact details', type: 'text', showInGrid: false },

    { key: 'area', label: 'Area', type: 'text', showInGrid: false },
    { key: 'unit_type', label: 'Unit type', type: 'text', showInGrid: false },
    { key: 'building_name', label: 'Building name', type: 'text', showInGrid: false },
    { key: 'bedrooms', label: 'No. of bedrooms', type: 'number', showInGrid: false },
    { key: 'street_name', label: 'Street name', type: 'text', showInGrid: false },
    { key: 'unit_number', label: 'Unit number', type: 'text', showInGrid: false },
    { key: 'street_number', label: 'Street number', type: 'text', showInGrid: false },
    { key: 'dewa_number', label: 'DEWA number', type: 'text', showInGrid: false },

    { key: 'lease_start_date', label: 'Lease start date', type: 'date', showInGrid: false },
    { key: 'lease_expiry_date', label: 'Lease expiry date', type: 'date', showInGrid: false },
    { key: 'plot_number', label: 'Plot number', type: 'text', showInGrid: false },
    { key: 'unit_category', label: 'Unit category', type: 'text', showInGrid: false },

    { key: 'issue_date', label: 'Issue date', type: 'date', gridWidth: 120 },
    { key: 'expiry_date', label: 'Expiry date', type: 'date', gridWidth: 120 },
    { key: 'fee', label: 'Fee (AED)', type: 'number', gridValueFormatter: formatAmount },
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
      gridWidth: 110,
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
