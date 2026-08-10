import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Plan §3.3 `product_line_conversion` (doc §1.9) -- checklist detail per step is a
 * dedicated workflow screen once this milestone is built; this is the header record. */
export const CONVERSIONS_CONFIG: EntityPageConfig = {
  title: 'Product-Line Conversions',
  subtitle: 'Header record for a unit switching long-term ↔ short-term (doc §1.9). Step-by-step checklist lands as its own workflow screen later.',
  resourcePath: 'product-line-conversions',
  fields: [
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    {
      key: 'direction',
      label: 'Direction',
      type: 'select',
      required: true,
      options: [
        { label: 'Long-term → Short-term', value: 'lt_to_st' },
        { label: 'Short-term → Long-term', value: 'st_to_lt' },
      ],
    },
    { key: 'started_at', label: 'Started', type: 'date' },
    { key: 'completed_at', label: 'Completed', type: 'date' },
    { key: 'idle_days', label: 'Idle days', type: 'number', gridWidth: 110 },
    { key: 'total_cost', label: 'Total cost (AED)', type: 'number' },
  ],
};
