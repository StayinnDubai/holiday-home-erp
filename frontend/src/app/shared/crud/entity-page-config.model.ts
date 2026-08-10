export type FieldType =
  | 'text'
  | 'number'
  | 'boolean'
  | 'date'
  | 'select'
  | 'textarea'
  /** Single FK picked from another resource's list, e.g. a unit's building. */
  | 'relation-select'
  /** Many-to-many picked from another resource's list, e.g. a unit's landlords. */
  | 'relation-multiselect';

export interface SelectOption {
  label: string;
  value: string;
}

export interface EntityFieldConfig {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  /** Static options, for type 'select'. */
  options?: SelectOption[];
  /** For 'relation-select' / 'relation-multiselect': resource path options are loaded from, e.g. 'buildings'. */
  relationResourcePath?: string;
  /** Field on the related record to show as the option label. Defaults to 'name'. */
  relationLabelKey?: string;
  /** Field on the related record to use as the option value. Defaults to 'id'. */
  relationValueKey?: string;
  /** For 'relation-select' / 'relation-multiselect': if set, the dropdown gets a
   * "+ Create new" option that opens an inline quick-create form using these fields
   * (typically another module's own EntityPageConfig.fields, reused as-is) -- so e.g.
   * a Building can be created without leaving the Unit form. Posts to relationResourcePath. */
  relationCreateFields?: EntityFieldConfig[];
  /** Label for the quick-create option/dialog, e.g. "Building". Defaults to the field's label. */
  relationCreateLabel?: string;
  /** ag-Grid column width in px. Omit to let the grid auto-size / flex. */
  gridWidth?: number;
  /** Defaults to true. Set false to keep a field (e.g. an id) out of the grid. */
  showInGrid?: boolean;
  /** Defaults to true. Set false for grid-only/derived fields (e.g. created_at). */
  showInForm?: boolean;
  /** Grid-only formatter, e.g. for booleans or enums -- avoids raw `true`/`false`/codes. */
  gridValueFormatter?: (value: unknown) => string;
}

export interface EntityPageConfig {
  title: string;
  subtitle?: string;
  /** REST resource path, e.g. 'units' -> /api/v1/units (backend/app/core/pagination.py contract). */
  resourcePath: string;
  fields: EntityFieldConfig[];
  /** Extra fixed query params on every list call, e.g. { list_name: 'block_type' }. */
  extraListParams?: Record<string, string>;
  /** Extra fixed fields merged into every create payload, e.g. a filter this page is scoped to. */
  extraCreatePayload?: Record<string, unknown>;
  pageSize?: number;
}
