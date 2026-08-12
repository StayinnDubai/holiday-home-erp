import { CommonModule } from '@angular/common';
import { Component, OnInit, ViewChild, signal } from '@angular/core';
import type { ColDef } from 'ag-grid-community';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { map } from 'rxjs';
import { CrudApiService } from '../../core/api/crud-api.service';
import { ListQuery } from '../../core/models/api.model';
import { AgGridTableComponent } from '../../shared/ag-grid/ag-grid-table.component';
import { EntityFieldConfig, FieldType } from '../../shared/crud/entity-page-config.model';
import { EntityFormComponent } from '../../shared/crud/entity-form.component';
import { RowActionsCellRendererComponent, RowActionsContext } from '../../shared/crud/row-actions-cell-renderer.component';

interface BankAccountOption {
  id: string;
  code: string;
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
 * Accounting > Bank Statement - Reconciliation. Same underlying mechanism as Bank
 * Statement - Original (bank-statement-original.component.ts's sibling) -- no
 * fixed columns at all, each bank account defines its own column set in Settings >
 * Bank Account Columns (tagged `applies_to: 'reconciliation'` there, `kind:
 * 'reconciliation'` on the entries themselves), since banks export statements in
 * different shapes. Bespoke component rather than EntityPageComponent because the
 * field list (and therefore the grid columns and the add/edit form) is only known
 * once a bank account is picked, from the account-switcher row at the bottom.
 * Original uses a header dropdown instead of a bottom switcher -- the only UX
 * difference between the two, per how each was asked for.
 *
 * `BankStatementEntry.values` is a JSONB blob keyed by column `key`. Rows are
 * flattened (`{...row, ...row.values}`) before being handed to AgGridTableComponent /
 * EntityFormComponent so both can be reused unmodified -- they already expect a flat
 * `Record<string, unknown>` keyed by each field's `key`.
 */
@Component({
  selector: 'app-bank-statement-reconciliation',
  standalone: true,
  imports: [CommonModule, ButtonModule, ConfirmDialogModule, DialogModule, AgGridTableComponent, EntityFormComponent],
  providers: [ConfirmationService],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Bank Statement - Reconciliation</h2>
          <p class="panel__subtitle">
            {{ selectedAccount ? 'Showing ' + accountLabel(selectedAccount) : 'Pick a bank account below.' }}
          </p>
        </div>
        <p-button label="Add new" icon="pi pi-plus" (onClick)="openCreate()" [disabled]="!selectedAccount || columns.length === 0" />
      </div>

      <div class="panel__grid" *ngIf="selectedAccount; else noAccount">
        <p class="panel__hint" *ngIf="columns.length === 0">
          No columns configured for this bank account yet -- add some under Settings &gt; Bank Account Columns.
        </p>
        <app-ag-grid-table
          #grid
          *ngIf="columns.length > 0"
          [columnDefs]="columnDefs"
          [fetchPage]="fetchPage"
          [context]="gridContext"
        />
      </div>
      <ng-template #noAccount>
        <div class="panel__grid">
          <p class="panel__hint">No bank accounts yet -- add one under Accounting &gt; Bank Accounts.</p>
        </div>
      </ng-template>

      <div class="panel__switcher" *ngIf="accounts.length > 0">
        <button
          type="button"
          class="switcher__btn"
          *ngFor="let acct of accounts"
          [class.switcher__btn--active]="acct.id === selectedAccount?.id"
          (click)="selectAccount(acct)"
        >
          {{ accountLabel(acct) }}
        </button>
      </div>
    </div>

    <p-dialog
      [header]="editing() ? 'Edit reconciliation line' : 'Add reconciliation line'"
      [(visible)]="dialogVisible"
      [modal]="true"
      [dismissableMask]="true"
      [style]="{ width: '32rem' }"
    >
      <app-entity-form
        *ngIf="dialogVisible"
        [fields]="formFields"
        [model]="editing()"
        (save)="onSave($event)"
        (cancel)="dialogVisible = false"
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
      .panel__switcher {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 1rem 1.5rem;
        border-top: 1px solid #e2e8f0;
        flex-shrink: 0;
      }
      .switcher__btn {
        border: 1px solid #cbd5e1;
        background: #f8fafc;
        color: #334155;
        border-radius: 999px;
        padding: 0.45rem 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
      }
      .switcher__btn:hover {
        background: #eef2f7;
      }
      .switcher__btn--active {
        background: #0f766e;
        border-color: #0f766e;
        color: #fff;
      }
    `,
  ],
})
export class BankStatementReconciliationComponent implements OnInit {
  @ViewChild('grid') grid?: AgGridTableComponent<Row>;

  accounts: BankAccountOption[] = [];
  selectedAccount: BankAccountOption | null = null;
  columns: BankAccountColumnRow[] = [];
  columnDefs: ColDef[] = [];
  formFields: EntityFieldConfig[] = [];

  dialogVisible = false;
  editing = signal<Row | null>(null);

  readonly gridContext: RowActionsContext<Row> = {
    onEdit: (row) => this.openEdit(row),
    onDelete: (row) => this.confirmDelete(row),
  };

  fetchPage = (query: ListQuery) =>
    this.api
      .list<Row>(
        'bank-statement-entries',
        query,
        this.selectedAccount
          ? { bank_account_id: this.selectedAccount.id, kind: 'reconciliation' }
          : { kind: 'reconciliation' }
      )
      .pipe(map((res) => ({ ...res, data: res.data.map((row) => ({ ...row, ...row.values })) })));

  constructor(private readonly api: CrudApiService, private readonly confirmationService: ConfirmationService) {}

  ngOnInit(): void {
    this.api.list<BankAccountOption>('bank-accounts', { page: 1, page_size: 200 }).subscribe({
      next: (res) => {
        this.accounts = res.data;
        if (this.accounts.length > 0) {
          this.selectAccount(this.accounts[0]);
        }
      },
    });
  }

  accountLabel(acct: BankAccountOption): string {
    return `${acct.bank_name ?? 'Unknown bank'} - ${acct.currency_name ?? ''}`.trim();
  }

  selectAccount(acct: BankAccountOption): void {
    this.selectedAccount = acct;
    this.api
      .list<BankAccountColumnRow>(
        'bank-account-columns',
        { page: 1, page_size: 200, sort_by: 'sort_order' },
        { bank_account_id: acct.id, applies_to: 'reconciliation' }
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
              (f): ColDef => ({ field: f.key, headerName: f.label, minWidth: f.gridWidth ?? 140, flex: 1 })
            ),
            {
              headerName: 'Actions',
              width: 110,
              sortable: false,
              filter: false,
              resizable: false,
              cellRenderer: RowActionsCellRendererComponent,
            },
          ];
          // Column set just changed -- purge so the grid re-fetches under the new filter/columns.
          this.grid?.refresh();
        },
      });
  }

  openCreate(): void {
    this.editing.set(null);
    this.dialogVisible = true;
  }

  openEdit(row: Row): void {
    this.editing.set(row);
    this.dialogVisible = true;
  }

  onSave(payload: Record<string, unknown>): void {
    if (!this.selectedAccount) return;
    const body = { bank_account_id: this.selectedAccount.id, kind: 'reconciliation', values: payload };
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
      header: 'Delete reconciliation line',
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
}
