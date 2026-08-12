/** Formats a monetary amount with thousands separators for grid display, e.g.
 * 56000 -> '56,000', -1500.5 -> '-1,500.5'. Leaves non-numeric/empty values as
 * an empty cell rather than showing 'NaN' or 'null'. */
export function formatAmount(value: unknown): string {
  if (value === null || value === undefined || value === '') return '';
  const num = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
}
