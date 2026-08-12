import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CrudApiService } from '../../core/api/crud-api.service';

interface AuditLogEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
  action: string;
  reason: string | null;
  changed_by: string | null;
  changed_at: string;
}

const ACTION_LABELS: Record<string, string> = {
  create: 'Created',
  update: 'Updated',
  delete: 'Deleted',
  status_change: 'Status changed',
};

/**
 * Read-only change history for one record (doc §5.2) -- every service already calls
 * AuditService.log on create/update/delete with field-level old/new values, but nothing
 * in the frontend showed it until now. Dropped into EntityPageComponent's View dialog
 * (and the two bespoke Bank Statement view dialogs) rather than built as its own page,
 * since a history only means something in the context of one specific record.
 *
 * Backend's GET /audit-log takes `entity_type` + `entity_id` and returns every matching
 * row unpaginated (it's doc-scoped, not a global browsable log) -- CrudApiService.list()
 * still works here since the backend just ignores the page/page_size params it doesn't
 * recognize.
 */
@Component({
  selector: 'app-audit-history',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="audit-history">
      <h4 class="audit-history__title">History</h4>
      <p class="audit-history__state" *ngIf="loading">Loading history...</p>
      <p class="audit-history__state" *ngIf="!loading && entries.length === 0">No changes recorded yet.</p>
      <ul class="audit-history__list" *ngIf="!loading && entries.length > 0">
        <li class="audit-history__item" *ngFor="let e of entries">
          <div class="audit-history__row">
            <span class="audit-history__action" [class]="'audit-history__action--' + e.action">{{ actionLabel(e.action) }}</span>
            <span class="audit-history__field" *ngIf="e.field">{{ e.field }}</span>
            <span class="audit-history__time">{{ formatTime(e.changed_at) }}</span>
          </div>
          <div class="audit-history__diff" *ngIf="e.old_value !== null || e.new_value !== null">
            <span class="audit-history__old" *ngIf="e.old_value !== null">{{ e.old_value }}</span>
            <i class="pi pi-arrow-right" *ngIf="e.old_value !== null && e.new_value !== null"></i>
            <span class="audit-history__new" *ngIf="e.new_value !== null">{{ e.new_value }}</span>
          </div>
          <div class="audit-history__meta" *ngIf="e.changed_by || e.reason">
            <span *ngIf="e.changed_by">by {{ e.changed_by }}</span>
            <span *ngIf="e.reason">{{ e.changed_by ? ' — ' : '' }}{{ e.reason }}</span>
          </div>
        </li>
      </ul>
    </div>
  `,
  styles: [
    `
      .audit-history {
        margin-top: 1.25rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
      }
      .audit-history__title {
        margin: 0 0 0.6rem;
        font-size: 0.85rem;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
      .audit-history__state {
        margin: 0;
        font-size: 0.85rem;
        color: #94a3b8;
      }
      .audit-history__list {
        list-style: none;
        margin: 0;
        padding: 0;
        max-height: 16rem;
        overflow-y: auto;
      }
      .audit-history__item {
        padding: 0.55rem 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.82rem;
      }
      .audit-history__item:last-child {
        border-bottom: none;
      }
      .audit-history__row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .audit-history__action {
        font-weight: 700;
        padding: 0.1rem 0.5rem;
        border-radius: 999px;
        font-size: 0.72rem;
        background: #f1f5f9;
        color: #334155;
      }
      .audit-history__action--create {
        background: #dcfce7;
        color: #166534;
      }
      .audit-history__action--update,
      .audit-history__action--status_change {
        background: #e0f2fe;
        color: #075985;
      }
      .audit-history__action--delete {
        background: #fee2e2;
        color: #991b1b;
      }
      .audit-history__field {
        font-weight: 600;
        color: #475569;
      }
      .audit-history__time {
        margin-left: auto;
        color: #94a3b8;
        font-size: 0.78rem;
        white-space: nowrap;
      }
      .audit-history__diff {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-top: 0.3rem;
        color: #334155;
        flex-wrap: wrap;
      }
      .audit-history__old {
        text-decoration: line-through;
        color: #94a3b8;
      }
      .audit-history__new {
        font-weight: 600;
      }
      .audit-history__meta {
        margin-top: 0.2rem;
        color: #94a3b8;
        font-size: 0.78rem;
      }
    `,
  ],
})
export class AuditHistoryComponent implements OnChanges {
  @Input({ required: true }) entityType!: string;
  @Input({ required: true }) entityId!: string;

  entries: AuditLogEntry[] = [];
  loading = false;

  constructor(private readonly api: CrudApiService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entityType'] || changes['entityId']) {
      this.load();
    }
  }

  actionLabel(action: string): string {
    return ACTION_LABELS[action] ?? action;
  }

  formatTime(iso: string): string {
    return new Date(iso).toLocaleString();
  }

  private load(): void {
    if (!this.entityType || !this.entityId) return;
    this.loading = true;
    this.api
      .list<AuditLogEntry>('audit-log', { page: 1, page_size: 200 }, { entity_type: this.entityType, entity_id: this.entityId })
      .subscribe({
        next: (res) => {
          this.entries = res.data;
          this.loading = false;
        },
        error: () => {
          this.loading = false;
        },
      });
  }
}
