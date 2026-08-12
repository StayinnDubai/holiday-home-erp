import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';
import { formatAmount } from '../../shared/utils/amount';

/** Plan §3.4 `reservation` -- header fields; folio lines are a detail tab later.
 * Calendar view (doc §5.1) is a different UI paradigm, added separately -- this is the
 * list side of "Reservation List / Calendar". */
export const RESERVATIONS_CONFIG: EntityPageConfig = {
  title: 'Reservations',
  subtitle: 'Manual entry in v1 (doc D-3/D-8). Calendar view is a separate screen, added later.',
  resourcePath: 'reservations',
  fields: [
    { key: 'reservation_number', label: 'Reservation #', type: 'text', gridWidth: 150 },
    {
      key: 'channel',
      label: 'Channel',
      type: 'select',
      required: true,
      options: [
        { label: 'Booking.com', value: 'booking_com' },
        { label: 'Airbnb', value: 'airbnb' },
        { label: 'Direct', value: 'direct' },
      ],
    },
    { key: 'unit_id', label: 'Unit ID', type: 'text', required: true },
    { key: 'guest_id', label: 'Guest ID', type: 'text' },
    { key: 'check_in', label: 'Check-in', type: 'date', required: true },
    { key: 'check_out', label: 'Check-out', type: 'date', required: true },
    { key: 'gross_amount', label: 'Gross amount (AED)', type: 'number', gridValueFormatter: formatAmount },
    { key: 'net_amount', label: 'Net amount (AED)', type: 'number', gridValueFormatter: formatAmount },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Enquiry', value: 'enquiry' },
        { label: 'Tentative', value: 'tentative' },
        { label: 'Confirmed', value: 'confirmed' },
        { label: 'Checked in', value: 'checked_in' },
        { label: 'Checked out', value: 'checked_out' },
        { label: 'Cancelled', value: 'cancelled' },
        { label: 'No-show', value: 'no_show' },
      ],
    },
  ],
};

/** Plan §3.4 `guest`. */
export const GUESTS_CONFIG: EntityPageConfig = {
  title: 'Guests',
  subtitle: 'Doc §5.4. ID documents are the most sensitive data in the system -- field-level access control lands with auth (plan §7).',
  resourcePath: 'guests',
  fields: [
    { key: 'name', label: 'Name', type: 'text', required: true, gridWidth: 220 },
    { key: 'nationality', label: 'Nationality', type: 'text' },
    { key: 'passport_or_eid', label: 'Passport / Emirates ID', type: 'text' },
    { key: 'dob', label: 'Date of birth', type: 'date' },
    { key: 'contact', label: 'Contact', type: 'text' },
  ],
};
