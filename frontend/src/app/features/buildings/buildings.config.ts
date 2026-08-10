import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Header fields (plan §3.2 `building` table), plus `unit_count` -- a backend-computed
 * column (count of units with this building_id) proving the reverse of "one building per
 * unit": a building holds one-or-more units. Contacts, amenities, and deposits get their
 * own tabs once that part of the Buildings backend milestone is built. */
export const BUILDINGS_CONFIG: EntityPageConfig = {
  title: 'Buildings',
  subtitle: 'Header fields for now -- contacts, amenities, and deposits land as tabs later. "Units" is a live count of units in this building.',
  resourcePath: 'buildings',
  fields: [
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'unit_count', label: 'Units', type: 'number', showInForm: false, gridWidth: 90 },
    { key: 'developer', label: 'Developer', type: 'text' },
    { key: 'community', label: 'Community / area', type: 'text' },
    { key: 'address', label: 'Address', type: 'text', showInGrid: false },
    { key: 'makani', label: 'Makani', type: 'text', gridWidth: 130 },
    { key: 'floors', label: 'Floors', type: 'number', gridWidth: 100 },
    { key: 'year_built', label: 'Year built', type: 'number', gridWidth: 110 },
    {
      key: 'short_term_permitted',
      label: 'Short-term permitted',
      type: 'select',
      required: true,
      options: [
        { label: 'Yes', value: 'yes' },
        { label: 'No', value: 'no' },
        { label: 'Conditional', value: 'conditional' },
      ],
    },
  ],
};
