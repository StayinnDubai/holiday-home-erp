import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { CrudApiService } from '../../core/api/crud-api.service';

interface UnitSpaceRow {
  id: string;
  unit_id: string;
  space_type: string;
  name: string | null;
  notes: string | null;
}

const SPACE_TYPES = [
  { label: 'Bedroom', value: 'bedroom' },
  { label: 'Bathroom', value: 'bathroom' },
  { label: 'Living room', value: 'living_room' },
  { label: 'Kitchen', value: 'kitchen' },
  { label: 'Laundry area', value: 'laundry_area' },
  { label: 'Balcony', value: 'balcony' },
  { label: 'Storage', value: 'storage' },
  { label: 'Dining room', value: 'dining_room' },
  { label: 'Office', value: 'office' },
  { label: 'Other', value: 'other' },
];

/**
 * Unit layout components (doc §1.1 `UnitSpace`) -- "so a physical verification can
 * be done room by room." Small inline add/edit/delete list scoped to one unit, e.g.
 * Bedroom 1, Bedroom 2, Kitchen, Balcony. Separate from the unit-level `has_balcony`
 * flag -- that's a quick yes/no filter, this is the detailed room-by-room list.
 */
@Component({
  selector: 'app-unit-spaces-field',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ButtonModule, ConfirmDialogModule, DialogModule, InputTextModule, SelectModule, TextareaModule],
  providers: [ConfirmationService],
  template: `
    <div class="unit-spaces">
      <table class="unit-spaces__table" *ngIf="spaces.length">
        <thead>
          <tr>
            <th>Type</th>
            <th>Name</th>
            <th class="unit-spaces__actions-col"></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let s of spaces">
            <td>{{ typeLabel(s.space_type) }}</td>
            <td>{{ s.name || '—' }}</td>
            <td class="unit-spaces__actions">
              <button type="button" title="Edit" (click)="openEdit(s)"><i class="pi pi-pencil"></i></button>
              <button type="button" title="Delete" (click)="confirmDelete(s)"><i class="pi pi-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="unit-spaces__empty" *ngIf="!spaces.length && !loading">No layout components added yet.</p>

      <p-button label="Add space" icon="pi pi-plus" size="small" [text]="true" type="button" (onClick)="openCreate()" />
    </div>

    <p-dialog [header]="editing ? 'Edit space' : 'Add space'" [(visible)]="dialogVisible" [modal]="true" [dismissableMask]="true" [style]="{ width: '24rem' }">
      <form *ngIf="form" [formGroup]="form" (ngSubmit)="save()" class="unit-spaces__form">
        <label for="space_type">Type<span class="req">*</span></label>
        <p-select inputId="space_type" formControlName="space_type" [options]="spaceTypes" optionLabel="label" optionValue="value" />

        <label for="name">Name</label>
        <input id="name" pInputText formControlName="name" placeholder="e.g. Bedroom 1" />

        <label for="notes">Notes</label>
        <textarea id="notes" pTextarea formControlName="notes" rows="2"></textarea>

        <div class="unit-spaces__form-actions">
          <p-button label="Cancel" severity="secondary" [text]="true" type="button" (onClick)="dialogVisible = false" />
          <p-button label="Save" icon="pi pi-check" type="submit" [disabled]="form.invalid" />
        </div>
      </form>
    </p-dialog>

    <p-confirmDialog [style]="{ width: '26rem' }" icon="pi pi-exclamation-triangle" />
  `,
  styles: [
    `
      .unit-spaces {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }
      .unit-spaces__table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
      }
      .unit-spaces__table th {
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #64748b;
        border-bottom: 1px solid #e2e8f0;
        padding: 0.5rem 0.5rem;
      }
      .unit-spaces__table td {
        padding: 0.5rem 0.5rem;
        border-bottom: 1px solid #f1f5f9;
        color: #0f172a;
      }
      .unit-spaces__actions-col {
        width: 5rem;
      }
      .unit-spaces__actions {
        display: flex;
        gap: 0.4rem;
      }
      .unit-spaces__actions button {
        border: none;
        background: transparent;
        color: #64748b;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 6px;
      }
      .unit-spaces__actions button:hover {
        background: #f1f5f9;
        color: #0f172a;
      }
      .unit-spaces__empty {
        margin: 0;
        color: #64748b;
        font-size: 0.85rem;
      }
      .unit-spaces__form {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .unit-spaces__form label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
        margin-top: 0.5rem;
      }
      .unit-spaces__form .req {
        color: #dc2626;
      }
      .unit-spaces__form-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.75rem;
      }
    `,
  ],
})
export class UnitSpacesFieldComponent implements OnChanges {
  @Input({ required: true }) unitId!: string;

  spaceTypes = SPACE_TYPES;
  spaces: UnitSpaceRow[] = [];
  loading = false;

  dialogVisible = false;
  editing: UnitSpaceRow | null = null;
  form: FormGroup | null = null;

  constructor(private readonly api: CrudApiService, private readonly fb: FormBuilder, private readonly confirmationService: ConfirmationService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['unitId'] && this.unitId) {
      this.refresh();
    }
  }

  private refresh(): void {
    this.loading = true;
    this.api.list<UnitSpaceRow>('unit-spaces', { page: 1, page_size: 100 }, { unit_id: this.unitId }).subscribe({
      next: (res) => {
        this.spaces = res.data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  typeLabel(value: string): string {
    return this.spaceTypes.find((t) => t.value === value)?.label ?? value;
  }

  openCreate(): void {
    this.editing = null;
    this.form = this.fb.group({
      space_type: ['bedroom', Validators.required],
      name: [''],
      notes: [''],
    });
    this.dialogVisible = true;
  }

  openEdit(space: UnitSpaceRow): void {
    this.editing = space;
    this.form = this.fb.group({
      space_type: [space.space_type, Validators.required],
      name: [space.name],
      notes: [space.notes],
    });
    this.dialogVisible = true;
  }

  save(): void {
    if (!this.form || this.form.invalid) return;
    const payload = { unit_id: this.unitId, ...this.form.getRawValue() };

    const request = this.editing
      ? this.api.update<UnitSpaceRow>('unit-spaces', this.editing.id, payload)
      : this.api.create<UnitSpaceRow>('unit-spaces', payload);

    request.subscribe({
      next: () => {
        this.dialogVisible = false;
        this.refresh();
      },
    });
  }

  confirmDelete(space: UnitSpaceRow): void {
    this.confirmationService.confirm({
      header: 'Delete space',
      message: `Remove "${space.name || this.typeLabel(space.space_type)}" from this unit's layout?`,
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => {
        this.api.remove('unit-spaces', space.id).subscribe({
          next: () => this.refresh(),
        });
      },
    });
  }
}
