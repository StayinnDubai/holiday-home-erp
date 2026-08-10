import { EntityPageConfig } from '../../shared/crud/entity-page-config.model';

/** Plan §3.4 `task`. This is the list/grid side of "Task Board" -- a real drag-drop
 * Kanban board is a different UI paradigm and is layered on top of the same backend
 * later; the Task Calendar view is likewise separate. */
export const TASKS_CONFIG: EntityPageConfig = {
  title: 'Task Board',
  subtitle: 'Grid view for now; drag-drop board and calendar views are layered on the same data later (doc Section 4).',
  resourcePath: 'tasks',
  fields: [
    { key: 'task_number', label: 'Task #', type: 'text', gridWidth: 120 },
    {
      key: 'type',
      label: 'Type',
      type: 'select',
      required: true,
      options: [
        { label: 'Checkout cleaning', value: 'checkout_cleaning' },
        { label: 'Cleaning (other)', value: 'cleaning_other' },
        { label: 'Maintenance', value: 'maintenance' },
        { label: 'Inspection', value: 'inspection' },
      ],
    },
    { key: 'title', label: 'Title', type: 'text', required: true, gridWidth: 220 },
    { key: 'unit_id', label: 'Unit ID', type: 'text' },
    { key: 'assignee_name', label: 'Assignee', type: 'text' },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      options: [
        { label: 'Low', value: 'low' },
        { label: 'Standard', value: 'standard' },
        { label: 'Urgent', value: 'urgent' },
      ],
    },
    { key: 'due_date', label: 'Due date', type: 'date' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Assigned', value: 'assigned' },
        { label: 'In progress', value: 'in_progress' },
        { label: 'Blocked', value: 'blocked' },
        { label: 'Completed', value: 'completed' },
        { label: 'Verified', value: 'verified' },
        { label: 'Closed', value: 'closed' },
        { label: 'Cancelled', value: 'cancelled' },
      ],
    },
  ],
};
