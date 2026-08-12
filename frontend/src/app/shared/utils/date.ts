/** Formats a Date as a local-calendar-day 'YYYY-MM-DD' string.
 *
 * `Date.toISOString()` converts to UTC first -- for any timezone ahead of UTC
 * (e.g. Asia/Dubai, UTC+4), a date picker's local midnight becomes the previous
 * day once shifted to UTC, so `toISOString().slice(0, 10)` silently saves the day
 * before whatever the user picked. Reading the Date's local getters instead (as
 * this does) avoids that UTC round-trip entirely. */
export function toLocalDateString(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** Parses a 'YYYY-MM-DD' string into a Date at local midnight for that calendar
 * day -- the counterpart to `toLocalDateString`. `new Date('YYYY-MM-DD')` parses
 * as UTC midnight per spec, which then renders as the *previous* day in any
 * timezone behind UTC once a date-picker component reads it back with local
 * getters; constructing from the individual parts avoids that UTC round-trip. */
export function fromLocalDateString(s: string): Date {
  const [year, month, day] = s.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day);
}
