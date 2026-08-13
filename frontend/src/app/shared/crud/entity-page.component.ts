import { CommonModule } from '@angular/common';
import { Component, Input, OnInit, ViewChild, signal } from '@angular/core';
import type { ColDef } from 'ag-grid-community';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { forkJoin } from 'rxjs';
import { CrudApiService } from '../../core/api/crud-api.service';
import { ListQuery } from '../../core/models/api.model';
import { AgGridTableComponent } from '../ag-grid/ag-grid-table.component';
import { AuditHistoryComponent } from './audit-history.component';
import { EntityFieldConfig, EntityPageConfig } from './entity-page-config.model';
import { EntityFormComponent } from './entity-form.component';
import { filterTypeFor } from './grid-filter-type';
import { RowActionsCellRendererComponent, RowActionsContext } from './row-actions-cell-renderer.component';

type Row = Record<string, unknown> & { id: string };

/**
 * The generic list+form CRUD page every module routes to (plan §5, "grids everywhere,
 * with forms, add/edit/delete"). A module is just an EntityPageConfig -- see
 * features/*\/​*.config.ts -- not a bespoke component, so all ~25 modules share one
 * implementation instead of ~25 near-identical ones.
 *
 * Talks to the real planned REST contract (/api/v1/<resourcePath>, plan §4) even though
 * most backends don't exist yet -- the grid will show a connection error until its
 * module's backend milestone lands, which is the honest state rather than fake data.
 *
 * Delete confirmation uses PrimeNG's ConfirmDialog (not the native browser `confirm()`)
 * so it matches the rest of the app's styling instead of an unstyleable OS popup.
 * `ConfirmationService` is provided per-page-instance -- each EntityPageComponent gets
 * its own, which is the standard PrimeNG pattern for this.
 */
@Component({
  selector: 'app-entity-page',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    ConfirmDialogModule,
    DialogModule,
    AgGridTableComponent,
    EntityFormComponent,
    AuditHistoryComponent,
  ],
  providers: [ConfirmationService],
  template: `
    <div class="panel" [style.height]="embedded ? 'calc(100vh - 6.5rem - 3rem)' : 'calc(100vh - 6.5rem)'">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">{{ config.title }}</h2>
          <p class="panel__subtitle" *ngIf="config.subtitle">{{ config.subtitle }}</p>
        </div>
        <p-button label="Add new" icon="pi pi-plus" (onClick)="openCreate()" />
      </div>

      <div class="panel__grid">
        <app-ag-grid-table
          #grid
          [columnDefs]="columnDefs"
          [fetchPage]="fetchPage"
          [pageSize]="config.pageSize || 25"
          [context]="gridContext"
          [stateKey]="config.resourcePath"
          (rowView)="openView($event)"
          (bulkDelete)="onBulkDelete($event)"
          (cellEdited)="onCellEdited($event)"
        />
      </div>
    </div>

    <p-dialog
      [header]="dialogHeader()"
      [(visible)]="dialogVisible"
      [modal]="true"
      [dismissableMask]="true"
      [style]="{ width: '32rem' }"
    >
      <app-entity-form
        *ngIf="dialogVisible"
        [fields]="config.fields"
        [model]="editing()"
        [readonly]="viewing()"
        (save)="onSave($event)"
        (cancel)="dialogVisible = false"
      />
      <app-audit-history
        *ngIf="dialogVisible && viewing() && config.auditEntityType && editing() as row"
        [entityType]="config.auditEntityType"
        [entityId]="row.id"
      />
    </p-dialog>

    <p-confirmDialog [style]="{ width: '26rem' }" icon="pi pi-exclamation-triangle" />
  `,
  styles: [
    `
      .panel {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        min-height: 420px;
      }
      .panel__header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        flex-shrink: 0;
      }
      .panel__title {
        margin: 0 0 0.25rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
      }
      .panel__subtitle {
        margin: 0;
        color: #64748b;
        font-size: 0.88rem;
      }
      .panel__grid {
        flex: 1;
        min-height: 0;
        padding: 1rem;
      }
    `,
  ],
})
export class EntityPageComponent implements OnInit {
  @Input({ required: true }) config!: EntityPageConfig;
  /** Set by TabbedPageComponent when this page is nested inside a tab, instead of
   * being the sole content under the top bar -- accounts for the extra vertical
   * space PrimeNG's tab nav bar takes above it. Adjust the offset here if the tab
   * nav bar's actual height ever changes. */
  @Input() embedded = false;

  @ViewChild('grid') grid?: AgGridTableComponent<Row>;

  columnDefs: ColDef[] = [];
  dialogVisible = false;
  editing = signal<Row | null>(null);
  viewing = signal(false);

  readonly gridContext: RowActionsContext<Row> = {
    onView: (row) => this.openView(row),
    onEdit: (row) => this.openEdit(row),
    onDelete: (row) => this.confirmDelete(row),
  };

  fetchPage = (query: ListQuery) => this.api.list<Row>(this.config.resourcePath, query, this.config.extraListParams ?? {});

  constructor(private readonly api: CrudApiService, private readonly confirmationService: ConfirmationService) {}

  ngOnInit(): void {
    const gridFields = this.config.fields.filter((f: EntityFieldConfig) => f.showInGrid !== false);
    this.columnDefs = [
      ...gridFields.map(
        (f): ColDef => ({
          field: f.key,
          headerName: f.label,
          // `gridWidth` is a minimum, not a cap -- columns still flex to fill any
          // extra space, but never shrink below it and truncate their header/content
          // (a fixed `width` with several flex-only siblings was squeezing those down
          // to near-zero). Falls back to a size that fits most labels/values.
          minWidth: f.gridWidth ?? 140,
          flex: 1,
          sortable: f.sortable !== false,
          // Same gate as sortable: a computed/aggregate field with no join-backed
          // server-side match (sortable: false) can't be filtered server-side either
          // -- offering the filter UI there would silently do nothing.
          filter: f.sortable !== false ? filterTypeFor(f) : false,
          valueFormatter: f.gridValueFormatter ? (p) => f.gridValueFormatter!(p.value) : undefined,
          // Boolean flags (on-hold, active, ...) are low-risk to edit inline -- a single
          // toggle, no cross-field validation -- unlike text/number/select fields, which
          // keep going through the full form (required checks, unique-code validation,
          // etc. that only the modal enforces). Gated on the same `sortable` flag as
          // above: a computed boolean has nothing real to PATCH.
          ...(f.type === 'boolean' && f.sortable !== false
            ? { editable: true, cellRenderer: 'agCheckboxCellRenderer', cellEditor: 'agCheckboxCellEditor' }
            : {}),
        })
      ),
      {
        headerName: 'Actions',
        width: 150,
        pinned: 'right',
        sortable: false,
        filter: false,
        resizable: false,
        cellRenderer: RowActionsCellRendererComponent,
      },
    ];
  }

  dialogHeader(): string {
    if (this.viewing()) return 'View ' + this.config.title;
    return this.editing() ? 'Edit ' + this.config.title : 'Add ' + this.config.title;
  }

  openCreate(): void {
    this.editing.set(null);
    this.viewing.set(false);
    this.dialogVisible = true;
  }

  openView(row: Row): void {
    this.editing.set(row);
    this.viewing.set(true);
    this.dialogVisible = true;
  }

  openEdit(row: Row): void {
    this.editing.set(row);
    this.viewing.set(false);
    this.dialogVisible = true;
  }

  onSave(payload: Record<string, unknown>): void {
    const merged = { ...payload, ...(this.config.extraCreatePayload ?? {}) };
    const current = this.editing();
    const request = current
      ? this.api.update(this.config.resourcePath, current.id, merged)
      : this.api.create(this.config.resourcePath, merged);

    request.subscribe({
      next: () => {
        this.dialogVisible = false;
        this.grid?.refresh();
      },
    });
  }

  private rowLabel(row: Row): string {
    return String(row['name'] ?? row['label'] ?? row['unit_name'] ?? row['code'] ?? row['unit_code'] ?? row.id);
  }

  confirmDelete(row: Row): void {
    this.confirmationService.confirm({
      header: `Delete ${this.config.title.replace(/s$/, '')}`,
      message: `Are you sure you want to delete "${this.rowLabel(row)}"? This cannot be undone.`,
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => this.onDelete(row),
    });
  }

  private onDelete(row: Row): void {
    this.api.remove(this.config.resourcePath, row.id).subscribe({
      next: () => this.grid?.refresh(),
    });
  }

  onBulkDelete(rows: Row[]): void {
    if (rows.length === 0) return;
    this.confirmationService.confirm({
      header: `Delete ${rows.length} ${this.config.title}`,
      message: `Are you sure you want to delete ${rows.length} selected record(s)? This cannot be undone.`,
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => {
        forkJoin(rows.map((row) => this.api.remove(this.config.resourcePath, row.id))).subscribe({
          next: () => {
            this.grid?.refresh();
            this.grid?.clearSelection();
          },
          error: () => {
            // Interceptor already surfaced the failure as a toast -- refresh so the grid
            // reflects whichever rows did make it through before the failing one.
            this.grid?.refresh();
            this.grid?.clearSelection();
          },
        });
      },
    });
  }

  onCellEdited(evt: { data: Row; field: string; newValue: unknown }): void {
    this.api.update(this.config.resourcePath, evt.data.id, { [evt.field]: evt.newValue }).subscribe({
      // Re-fetch either way: on success to pick up any server-computed side effects, on
      // failure to snap the checkbox back to the server's actual value (the interceptor
      // already showed the error toast).
      next: () => this.grid?.refresh(),
      error: () => this.grid?.refresh(),
    });
  }
}
