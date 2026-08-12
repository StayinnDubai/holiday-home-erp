import { EntityFieldConfig } from './entity-page-config.model';

/** Maps a field's type to one of ag-Grid Community's free "provided simple filters"
 * -- `agSetColumnFilter` and the Columns/Filters tool panels are Enterprise-only,
 * but the per-column text/number/date filters used here aren't. Returns `false`
 * (no filter UI offered) for field types with no sensible column filter. */
export function filterTypeFor(field: EntityFieldConfig): string | false {
  switch (field.type) {
    case 'text':
    case 'select':
    case 'boolean':
      return 'agTextColumnFilter';
    case 'number':
      return 'agNumberColumnFilter';
    case 'date':
    case 'action-date':
      return 'agDateColumnFilter';
    default:
      return false;
  }
}
