import { CommonModule } from '@angular/common';
import { Component, OnInit, forwardRef } from '@angular/core';
import { FormBuilder, FormGroup, NG_VALUE_ACCESSOR, ReactiveFormsModule, Validators, ControlValueAccessor } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { CrudApiService } from '../../core/api/crud-api.service';
import { formatAmount } from '../utils/amount';

export interface JournalEntryLineRow {
  account_id: string;
  unit_id: string | null;
  debit: number;
  credit: number;
  description: string | null;
}

interface AccountOption {
  id: string;
  code: string;
  name: string;
}

interface UnitOption {
  id: string;
  unit_code: string;
}

/**
 * Debit/credit line editor for a Journal Entry -- unlike unit-spaces-field.component.ts's
 * (the pattern this mirrors visually), lines here are NOT a separately-persisted
 * sub-resource. A balanced entry only makes sense as one atomic set of lines, and the
 * balance/unit-dimension checks live server-side (JournalEntryService._validate_lines),
 * so lines travel with the rest of the form and get submitted together on Save --
 * this is why the component is a real ControlValueAccessor (like PrimeNG's own
 * p-multiselect) rather than talking to the API on its own.
 */
@Component({
  selector: 'app-journal-entry-lines-field',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    ConfirmDialogModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    SelectModule,
  ],
  providers: [
    ConfirmationService,
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => JournalEntryLinesFieldComponent), multi: true },
  ],
  template: `
    <div class="je-lines">
      <table class="je-lines__table" *ngIf="lines.length">
        <thead>
          <tr>
            <th>Account</th>
            <th>Unit</th>
            <th class="je-lines__num">Debit</th>
            <th class="je-lines__num">Credit</th>
            <th>Description</th>
            <th class="je-lines__actions-col"></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let l of lines; let i = index">
            <td>{{ accountLabel(l.account_id) }}</td>
            <td>{{ unitLabel(l.unit_id) }}</td>
            <td class="je-lines__num">{{ l.debit ? formatAmount(l.debit) : '' }}</td>
            <td class="je-lines__num">{{ l.credit ? formatAmount(l.credit) : '' }}</td>
            <td>{{ l.description || '—' }}</td>
            <td class="je-lines__actions">
              <button type="button" title="Edit" [disabled]="disabled" (click)="openEdit(i)"><i class="pi pi-pencil"></i></button>
              <button type="button" title="Delete" [disabled]="disabled" (click)="confirmDelete(i)"><i class="pi pi-trash"></i></button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr [class.je-lines__balanced]="isBalanced" [class.je-lines__unbalanced]="!isBalanced">
            <td colspan="2">{{ isBalanced ? 'Balanced' : 'Not balanced' }}</td>
            <td class="je-lines__num">{{ formatAmount(totalDebit) }}</td>
            <td class="je-lines__num">{{ formatAmount(totalCredit) }}</td>
            <td colspan="2"></td>
          </tr>
        </tfoot>
      </table>

      <p class="je-lines__empty" *ngIf="!lines.length">No lines added yet.</p>

      <p-button label="Add line" icon="pi pi-plus" size="small" [text]="true" type="button" [disabled]="disabled" (onClick)="openCreate()" />
    </div>

    <p-dialog
      [header]="editingIndex === null ? 'Add line' : 'Edit line'"
      [(visible)]="dialogVisible"
      [modal]="true"
      [dismissableMask]="true"
      [style]="{ width: '26rem' }"
    >
      <form *ngIf="form" [formGroup]="form" (ngSubmit)="saveLine()" class="je-lines__form">
        <label for="account_id">Account<span class="req">*</span></label>
        <p-select
          inputId="account_id"
          formControlName="account_id"
          [options]="accountOptions"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="Select..."
        />

        <label for="unit_id">Unit</label>
        <p-select
          inputId="unit_id"
          formControlName="unit_id"
          [options]="unitOptions"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          [showClear]="true"
          placeholder="None"
        />

        <label for="debit">Debit</label>
        <p-inputnumber inputId="debit" formControlName="debit" mode="decimal" [minFractionDigits]="2" />

        <label for="credit">Credit</label>
        <p-inputnumber inputId="credit" formControlName="credit" mode="decimal" [minFractionDigits]="2" />

        <label for="description">Description</label>
        <input id="description" pInputText formControlName="description" />

        <div class="je-lines__form-actions">
          <p-button label="Cancel" severity="secondary" [text]="true" type="button" (onClick)="dialogVisible = false" />
          <p-button label="Save" icon="pi pi-check" type="submit" [disabled]="form.invalid" />
        </div>
      </form>
    </p-dialog>

    <p-confirmDialog [style]="{ width: '26rem' }" icon="pi pi-exclamation-triangle" />
  `,
  styles: [
    `
      .je-lines {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }
      .je-lines__table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
      }
      .je-lines__table th {
        text-align: left;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #64748b;
        border-bottom: 1px solid #e2e8f0;
        padding: 0.4rem 0.4rem;
      }
      .je-lines__table td {
        padding: 0.4rem 0.4rem;
        border-bottom: 1px solid #f1f5f9;
        color: #0f172a;
      }
      .je-lines__num {
        text-align: right;
        white-space: nowrap;
      }
      .je-lines__actions-col {
        width: 4.5rem;
      }
      .je-lines__actions {
        display: flex;
        gap: 0.35rem;
      }
      .je-lines__actions button {
        border: none;
        background: transparent;
        color: #64748b;
        cursor: pointer;
        padding: 0.2rem;
        border-radius: 6px;
      }
      .je-lines__actions button:hover {
        background: #f1f5f9;
        color: #0f172a;
      }
      .je-lines__actions button:disabled,
      .je-lines ::ng-deep .p-button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      .je-lines__actions button:disabled:hover {
        background: transparent;
        color: #64748b;
      }
      .je-lines__balanced td {
        color: #166534;
        font-weight: 700;
      }
      .je-lines__unbalanced td {
        color: #b91c1c;
        font-weight: 700;
      }
      .je-lines__empty {
        margin: 0;
        color: #64748b;
        font-size: 0.85rem;
      }
      .je-lines__form {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .je-lines__form label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
        margin-top: 0.5rem;
      }
      .je-lines__form .req {
        color: #dc2626;
      }
      .je-lines__form-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.75rem;
      }
    `,
  ],
})
export class JournalEntryLinesFieldComponent implements OnInit, ControlValueAccessor {
  lines: JournalEntryLineRow[] = [];
  disabled = false;

  accounts: AccountOption[] = [];
  units: UnitOption[] = [];
  accountOptions: { label: string; value: string }[] = [];
  unitOptions: { label: string; value: string }[] = [];

  dialogVisible = false;
  editingIndex: number | null = null;
  form: FormGroup | null = null;

  private onChange: (value: JournalEntryLineRow[]) => void = () => {};
  private onTouched: () => void = () => {};

  constructor(private readonly api: CrudApiService, private readonly fb: FormBuilder, private readonly confirmationService: ConfirmationService) {}

  ngOnInit(): void {
    this.api.list<AccountOption>('accounts', { page: 1, page_size: 200, sort_by: 'code' }).subscribe({
      next: (res) => {
        this.accounts = res.data;
        this.accountOptions = res.data.map((a) => ({ label: `${a.code} - ${a.name}`, value: a.id }));
      },
    });
    this.api.list<UnitOption>('units', { page: 1, page_size: 200, sort_by: 'unit_code' }).subscribe({
      next: (res) => {
        this.units = res.data;
        this.unitOptions = res.data.map((u) => ({ label: u.unit_code, value: u.id }));
      },
    });
  }

  writeValue(value: JournalEntryLineRow[] | null): void {
    this.lines = value ?? [];
  }

  registerOnChange(fn: (value: JournalEntryLineRow[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  formatAmount = formatAmount;

  get totalDebit(): number {
    return this.lines.reduce((sum, l) => sum + (l.debit || 0), 0);
  }

  get totalCredit(): number {
    return this.lines.reduce((sum, l) => sum + (l.credit || 0), 0);
  }

  get isBalanced(): boolean {
    return this.lines.length > 0 && Math.abs(this.totalDebit - this.totalCredit) < 0.005;
  }

  accountLabel(accountId: string): string {
    const a = this.accounts.find((x) => x.id === accountId);
    return a ? `${a.code} - ${a.name}` : accountId;
  }

  unitLabel(unitId: string | null): string {
    if (!unitId) return '—';
    return this.units.find((u) => u.id === unitId)?.unit_code ?? unitId;
  }

  openCreate(): void {
    this.editingIndex = null;
    this.form = this.fb.group({
      account_id: [null, Validators.required],
      unit_id: [null],
      debit: [0],
      credit: [0],
      description: [''],
    });
    this.dialogVisible = true;
  }

  openEdit(index: number): void {
    this.editingIndex = index;
    const line = this.lines[index];
    this.form = this.fb.group({
      account_id: [line.account_id, Validators.required],
      unit_id: [line.unit_id],
      debit: [line.debit],
      credit: [line.credit],
      description: [line.description],
    });
    this.dialogVisible = true;
  }

  saveLine(): void {
    if (!this.form || this.form.invalid) return;
    const value = this.form.getRawValue() as JournalEntryLineRow;
    const next = [...this.lines];
    if (this.editingIndex === null) {
      next.push(value);
    } else {
      next[this.editingIndex] = value;
    }
    this.lines = next;
    this.emit();
    this.dialogVisible = false;
  }

  confirmDelete(index: number): void {
    this.confirmationService.confirm({
      header: 'Delete line',
      message: 'Remove this line from the entry?',
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => {
        this.lines = this.lines.filter((_, i) => i !== index);
        this.emit();
      },
    });
  }

  private emit(): void {
    this.onChange(this.lines);
    this.onTouched();
  }
}
