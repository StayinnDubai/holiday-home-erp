import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import type { ColDef } from 'ag-grid-community';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { SelectModule } from 'primeng/select';
import { forkJoin, map } from 'rxjs';
import { CrudApiService } from '../../core/api/crud-api.service';
import { ListQuery } from '../../core/models/api.model';
import { MatchSuggestion, ReconciliationApiService } from '../../core/api/reconciliation-api.service';
import { AgGridTableComponent } from '../../shared/ag-grid/ag-grid-table.component';
import { formatAmount } from '../../shared/utils/amount';
import { AuditHistoryComponent } from '../../shared/crud/audit-history.component';
import { EntityFieldConfig, FieldType } from '../../shared/crud/entity-page-config.model';
import { EntityFormComponent } from '../../shared/crud/entity-form.component';
import { filterTypeFor } from '../../shared/crud/grid-filter-type';
import { RowActionsCellRendererComponent, RowActionsContext } from '../../shared/crud/row-actions-cell-renderer.component';

interface BankAccountOption {
  id: string;
  bank_name: string | null;
  currency_name: string | null;
}

interface BankAccountColumnRow {
  id: string;
  key: string;
  label: string;
  data_type: 'text' | 'number' | 'date';
  sort_order: number;
}

type Row = Record<string, unknown> & { id: string; bank_account_id: string; values: Record<string, unknown> };

const COLUMN_TYPE_TO_FIELD_TYPE: Record<BankAccountColumnRow['data_type'], FieldType> = {
  text: 'text',
  number: 'number',
  date: 'date',
};

/**
 * Accounting > Bank Statement - Original. Same underlying mechanism as Bank
 * Statement - Reconciliation (bank-statement-original.component.ts's sibling) --
 * no fixed schema, each bank account defines its own column set in Settings >
 * Bank Account Columns (tagged `applies_to: 'original'` there, `kind: 'original'`
 * on the entries themselves) since banks export statements in different shapes.
 * The two views share the same `bank-statement-entries` resource and the same
 * `bank-account-columns` designer, kept apart by that `kind`/`applies_to` tag --
 * only the picker placement differs (header dropdown here vs. Reconciliation's
 * bottom button row), per how each was asked for.
 *
 * `BankStatementEntry.values` is a JSONB blob keyed by column `key`. Rows are
 * flattened (`{...row, ...row.values}`) before being handed to AgGridTableComponent
 * / EntityFormComponent so both can be reused unmodified -- they already expect a
 * flat `Record<string, unknown>` keyed by each field's `key`.
 */
@Component({
  selector: 'app-bank-statement-original',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    ConfirmDialogModule,
    DialogModule,
    SelectModule,
    AgGridTableComponent,
    EntityFormComponent,
    AuditHistoryComponent,
  ],
  providers: [ConfirmationService],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Bank Statement - Original</h2>
          <p class="panel__subtitle">Bank statement lines, entered manually (doc §5.9) -- columns are configured per bank account.</p>
        </div>
        <div class="panel__header-actions">
          <p-select
            [options]="accountOptions"
            [(ngModel)]="selectedAccountId"
            (onChange)="onAccountChange()"
            optionLabel="label"
            optionValue="value"
            placeholder="Select a bank account"
            [style]="{ width: '18rem' }"
          />
          <p-button
            label="Suggest matches"
            icon="pi pi-sync"
            severity="secondary"
            [outlined]="true"
            (onClick)="openSuggestMatches()"
            [disabled]="!selectedAccountId"
          />
          <p-button
            label="Add new"
            icon="pi pi-plus"
            (onClick)="openCreate()"
            [disabled]="!selectedAccountId || columns.length === 0"
          />
        </div>
      </div>

      <div class="panel__grid">
        <p class="panel__hint" *ngIf="!selectedAccountId">Pick a bank account above.</p>
        <p class="panel__hint" *ngIf="selectedAccountId && columns.length === 0">
          No columns configured for this bank account yet -- add some under Settings &gt; Bank Account Columns
          (View = "Bank Statement - Original").
        </p>
        <app-ag-grid-table
          #grid
          *ngIf="selectedAccountId && columns.length > 0"
          [columnDefs]="columnDefs"
          [fetchPage]="fetchPage"
          [context]="gridContext"
          [stateKey]="'bank-statement-original:' + selectedAccountId"
          (rowView)="openView($event)"
          (bulkDelete)="onBulkDelete($event)"
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
        [fields]="formFields"
        [model]="editing()"
        [readonly]="viewing()"
        (save)="onSave($event)"
        (cancel)="dialogVisible = false"
      />
      <app-audit-history *ngIf="dialogVisible && viewing() && editing() as row" entityType="bank_statement_entry" [entityId]="row.id" />
    </p-dialog>

    <p-confirmDialog [style]="{ width: '26rem' }" icon="pi pi-exclamation-triangle" />

    <p-dialog
      header="Suggested matches"
      [(visible)]="matchDialogVisible"
      [modal]="true"
      [dismissableMask]="true"
      [style]="{ width: '42rem' }"
    >
      <p class="panel__hint" *ngIf="matchLoading">Looking for matches...</p>
      <p class="panel__hint" *ngIf="!matchLoading && !matchConfigured">
        This account's Original columns aren't tagged for matching yet -- set an "Amount" and "Date" role under
        Settings &gt; Bank Account Columns first.
      </p>
      <p class="panel__hint" *ngIf="!matchLoading && matchConfigured && matchSuggestions.length === 0">
        No matches found -- either every open cheque is already matched, or none line up closely enough.
      </p>
      <table class="match-table" *ngIf="!matchLoading && matchSuggestions.length > 0">
        <thead>
          <tr>
            <th>Cheque</th>
            <th class="match-table__num">Amount</th>
            <th>Cheque date</th>
            <th>Statement date</th>
            <th class="match-table__num">Diff (days)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let s of matchSuggestions">
            <td>{{ s.cheque_number }}</td>
            <td class="match-table__num">{{ formatAmount(s.cheque_amount) }}</td>
            <td>{{ s.cheque_date }}</td>
            <td>{{ s.entry_date }}</td>
            <td class="match-table__num">{{ s.day_difference }}</td>
            <td class="match-table__actions">
              <p-button label="Confirm" size="small" (onClick)="confirmMatch(s)" />
              <p-button label="Skip" size="small" severity="secondary" [text]="true" (onClick)="skipMatch(s)" />
            </td>
          </tr>
        </tbody>
      </table>
    </p-dialog>
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
        height: calc(100vh - 6.5rem);
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
      .panel__header-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
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
        display: flex;
        flex-direction: column;
      }
      .panel__grid app-ag-grid-table {
        flex: 1;
        min-height: 0;
      }
      .panel__hint {
        color: #64748b;
        font-size: 0.9rem;
      }
      .match-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
      }
      .match-table th {
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #64748b;
        border-bottom: 2px solid #e2e8f0;
        padding: 0.5rem 0.6rem;
      }
      .match-table td {
        padding: 0.5rem 0.6rem;
        border-bottom: 1px solid #f1f5f9;
        color: #0f172a;
      }
      .match-table__num {
        text-align: right;
        white-space: nowrap;
      }
      .match-table__actions {
        display: flex;
        gap: 0.4rem;
        justify-content: flex-end;
      }
    `,
  ],
})
export class BankStatementOriginalComponent implements OnInit {
  @ViewChild('grid') grid?: AgGridTableComponent<Row>;

  accountOptions: { label: string; value: string }[] = [];
  selectedAccountId: string | null = null;
  columns: BankAccountColumnRow[] = [];
  columnDefs: ColDef[] = [];
  formFields: EntityFieldConfig[] = [];

  dialogVisible = false;
  editing = signal<Row | null>(null);
  viewing = signal(false);

  matchDialogVisible = false;
  matchLoading = false;
  matchConfigured = true;
  matchSuggestions: MatchSuggestion[] = [];
  formatAmount = formatAmount;

  readonly gridContext: RowActionsContext<Row> = {
    onView: (row) => this.openView(row),
    onEdit: (row) => this.openEdit(row),
    onDelete: (row) => this.confirmDelete(row),
  };

  fetchPage = (query: ListQuery) =>
    this.api
      .list<Row>(
        'bank-statement-entries',
        query,
        this.selectedAccountId ? { bank_account_id: this.selectedAccountId, kind: 'original' } : { kind: 'original' }
      )
      .pipe(map((res) => ({ ...res, data: res.data.map((row) => ({ ...row, ...row.values })) })));

  constructor(
    private readonly api: CrudApiService,
    private readonly reconciliationApi: ReconciliationApiService,
    private readonly confirmationService: ConfirmationService
  ) {}

  ngOnInit(): void {
    this.api.list<BankAccountOption>('bank-accounts', { page: 1, page_size: 200 }).subscribe({
      next: (res) => {
        this.accountOptions = res.data.map((a) => ({
          label: `${a.bank_name ?? 'Unknown bank'} - ${a.currency_name ?? ''}`.trim(),
          value: a.id,
        }));
        if (this.accountOptions.length > 0) {
          this.selectedAccountId = this.accountOptions[0].value;
          this.loadColumns();
        }
      },
    });
  }

  onAccountChange(): void {
    this.loadColumns();
  }

  private loadColumns(): void {
    if (!this.selectedAccountId) {
      this.columns = [];
      this.columnDefs = [];
      this.formFields = [];
      return;
    }
    this.api
      .list<BankAccountColumnRow>(
        'bank-account-columns',
        { page: 1, page_size: 200, sort_by: 'sort_order' },
        { bank_account_id: this.selectedAccountId, applies_to: 'original' }
      )
      .subscribe({
        next: (res) => {
          this.columns = res.data;
          this.formFields = this.columns.map(
            (c): EntityFieldConfig => ({
              key: c.key,
              label: c.label,
              type: COLUMN_TYPE_TO_FIELD_TYPE[c.data_type] ?? 'text',
              gridWidth: 160,
            })
          );
          this.columnDefs = [
            ...this.formFields.map(
              (f): ColDef => ({
                field: f.key,
                headerName: f.label,
                minWidth: f.gridWidth ?? 140,
                flex: 1,
                filter: filterTypeFor(f),
                // Every dynamic column here is a bank-statement figure (amount, balance,
                // debit, credit, ...) -- comma-group it like any other accounting number.
                valueFormatter: f.type === 'number' ? (p) => formatAmount(p.value) : undefined,
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
          // Account/column set just changed -- purge so the grid re-fetches under the new filter/columns.
          this.grid?.refresh();
        },
      });
  }

  dialogHeader(): string {
    if (this.viewing()) return 'View statement line';
    return this.editing() ? 'Edit statement line' : 'Add statement line';
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
    if (!this.selectedAccountId) return;
    const body = { bank_account_id: this.selectedAccountId, kind: 'original', values: payload };
    const current = this.editing();
    const request = current
      ? this.api.update('bank-statement-entries', current.id, body)
      : this.api.create('bank-statement-entries', body);

    request.subscribe({
      next: () => {
        this.dialogVisible = false;
        this.grid?.refresh();
      },
    });
  }

  confirmDelete(row: Row): void {
    this.confirmationService.confirm({
      header: 'Delete statement line',
      message: 'Are you sure you want to delete this line? This cannot be undone.',
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => this.onDelete(row),
    });
  }

  private onDelete(row: Row): void {
    this.api.remove('bank-statement-entries', row.id).subscribe({
      next: () => this.grid?.refresh(),
    });
  }

  openSuggestMatches(): void {
    if (!this.selectedAccountId) return;
    this.matchDialogVisible = true;
    this.matchLoading = true;
    this.reconciliationApi.matchSuggestions(this.selectedAccountId).subscribe({
      next: (res) => {
        this.matchConfigured = res.configured;
        this.matchSuggestions = res.suggestions;
        this.matchLoading = false;
      },
      error: () => {
        this.matchLoading = false;
      },
    });
  }

  confirmMatch(s: MatchSuggestion): void {
    this.api
      .update('cheques', s.cheque_id, {
        status: 'cleared',
        actual_drawdown_date: s.entry_date,
        drawdown_source: 'bank_reconciliation',
        matched_bank_statement_entry_id: s.bank_statement_entry_id,
      })
      .subscribe({
        next: () => {
          this.matchSuggestions = this.matchSuggestions.filter((x) => x.cheque_id !== s.cheque_id);
        },
      });
  }

  skipMatch(s: MatchSuggestion): void {
    this.matchSuggestions = this.matchSuggestions.filter((x) => x.cheque_id !== s.cheque_id);
  }

  onBulkDelete(rows: Row[]): void {
    if (rows.length === 0) return;
    this.confirmationService.confirm({
      header: `Delete ${rows.length} statement lines`,
      message: `Are you sure you want to delete ${rows.length} selected line(s)? This cannot be undone.`,
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => {
        forkJoin(rows.map((row) => this.api.remove('bank-statement-entries', row.id))).subscribe({
          next: () => {
            this.grid?.refresh();
            this.grid?.clearSelection();
          },
          error: () => {
            this.grid?.refresh();
            this.grid?.clearSelection();
          },
        });
      },
    });
  }
}
