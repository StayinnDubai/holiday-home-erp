import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { MultiSelectModule } from 'primeng/multiselect';
import { PrimeTemplate } from 'primeng/api';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { CrudApiService } from '../../core/api/crud-api.service';
import { EntityFieldConfig, SelectOption } from './entity-page-config.model';

function requiredArray(control: AbstractControl): ValidationErrors | null {
  return Array.isArray(control.value) && control.value.length > 0 ? null : { required: true };
}

/**
 * Renders a Reactive Form from an EntityFieldConfig[] (shared/crud/entity-page-config.model.ts)
 * instead of one bespoke form per module -- with ~25 modules, hand-writing a form each is
 * the same handful of input types every time. Deeper module-specific forms (multi-line
 * journal entries, unit ownership shares, etc.) replace this per module once the backend
 * for that module exists and the real shape is known.
 *
 * `relation-select` / `relation-multiselect` fields (e.g. a unit's building/landlords)
 * load their options live from another resource's list endpoint via CrudApiService, and
 * -- if `relationCreateFields` is configured -- offer a "+ Create new" option inside the
 * dropdown that opens a nested instance of this same component to create the related
 * record inline, without leaving the current form (e.g. adding a Building while adding
 * a Unit). The newly created record is added to the dropdown and selected automatically.
 */
@Component({
  selector: 'app-entity-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    CheckboxModule,
    DatePickerModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    MultiSelectModule,
    PrimeTemplate,
    SelectModule,
    TextareaModule,
    EntityFormComponent,
  ],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" class="entity-form">
      <div class="entity-form__field" *ngFor="let field of formFields">
        <label [for]="field.key">{{ field.label }}<span *ngIf="field.required" class="req">*</span></label>

        <input
          *ngIf="field.type === 'text'"
          pInputText
          [id]="field.key"
          [formControlName]="field.key"
        />

        <p-inputnumber *ngIf="field.type === 'number'" [inputId]="field.key" [formControlName]="field.key" />

        <p-checkbox *ngIf="field.type === 'boolean'" [inputId]="field.key" [formControlName]="field.key" [binary]="true" />

        <p-datepicker *ngIf="field.type === 'date'" [inputId]="field.key" [formControlName]="field.key" dateFormat="yy-mm-dd" />

        <p-select
          *ngIf="field.type === 'select'"
          [inputId]="field.key"
          [formControlName]="field.key"
          [options]="field.options"
          optionLabel="label"
          optionValue="value"
          [showClear]="!field.required"
        />

        <p-select
          *ngIf="field.type === 'relation-select'"
          [inputId]="field.key"
          [formControlName]="field.key"
          [options]="relationOptions[field.key] || []"
          [loading]="relationLoading[field.key]"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          [showClear]="!field.required"
          placeholder="Select..."
        >
          <ng-template pTemplate="footer" *ngIf="field.relationCreateFields">
            <div class="entity-form__quick-create-footer">
              <p-button
                [label]="'+ Create new ' + (field.relationCreateLabel || field.label)"
                [text]="true"
                size="small"
                type="button"
                (onClick)="openQuickCreate(field)"
              />
            </div>
          </ng-template>
        </p-select>

        <p-multiselect
          *ngIf="field.type === 'relation-multiselect'"
          [inputId]="field.key"
          [formControlName]="field.key"
          [options]="relationOptions[field.key] || []"
          [loading]="relationLoading[field.key]"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          display="chip"
          placeholder="Select..."
        >
          <ng-template pTemplate="footer" *ngIf="field.relationCreateFields">
            <div class="entity-form__quick-create-footer">
              <p-button
                [label]="'+ Create new ' + (field.relationCreateLabel || field.label)"
                [text]="true"
                size="small"
                type="button"
                (onClick)="openQuickCreate(field)"
              />
            </div>
          </ng-template>
        </p-multiselect>

        <textarea *ngIf="field.type === 'textarea'" pTextarea [id]="field.key" [formControlName]="field.key" rows="3"></textarea>
      </div>

      <div class="entity-form__actions">
        <p-button label="Cancel" severity="secondary" [text]="true" type="button" (onClick)="cancel.emit()" />
        <p-button label="Save" icon="pi pi-check" type="submit" [disabled]="form.invalid" />
      </div>
    </form>

    <p-dialog
      [header]="'Create new ' + (quickCreateField?.relationCreateLabel || quickCreateField?.label || '')"
      [(visible)]="quickCreateVisible"
      [modal]="true"
      [dismissableMask]="true"
      [style]="{ width: '28rem' }"
    >
      <app-entity-form
        *ngIf="quickCreateVisible && quickCreateField"
        [fields]="quickCreateField.relationCreateFields || []"
        [model]="null"
        (save)="onQuickCreateSave($event)"
        (cancel)="quickCreateVisible = false"
      />
    </p-dialog>
  `,
  styles: [
    `
      .entity-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-width: 22rem;
      }
      .entity-form__field {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .entity-form__field label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
      }
      .entity-form__field .req {
        color: #dc2626;
        margin-left: 0.15rem;
      }
      .entity-form__field input[pInputText],
      .entity-form__field p-inputnumber,
      .entity-form__field p-select,
      .entity-form__field p-multiselect,
      .entity-form__field p-datepicker,
      .entity-form__field textarea {
        width: 100%;
      }
      .entity-form__actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
      }
      .entity-form__quick-create-footer {
        border-top: 1px solid #e2e8f0;
        padding: 0.35rem;
      }
      .entity-form__quick-create-footer p-button {
        display: block;
      }
    `,
  ],
})
export class EntityFormComponent<T extends Record<string, unknown>> implements OnChanges {
  @Input({ required: true }) fields: EntityFieldConfig[] = [];
  /** Existing record for edit, or null/undefined for a new record. */
  @Input() model: T | null = null;

  @Output() save = new EventEmitter<Record<string, unknown>>();
  @Output() cancel = new EventEmitter<void>();

  form: FormGroup = new FormGroup({});
  relationOptions: Record<string, SelectOption[]> = {};
  relationLoading: Record<string, boolean> = {};

  quickCreateField: EntityFieldConfig | null = null;
  quickCreateVisible = false;

  constructor(private readonly fb: FormBuilder, private readonly api: CrudApiService) {}

  get formFields(): EntityFieldConfig[] {
    return this.fields.filter((f) => f.showInForm !== false);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fields']) {
      this.loadAllRelationOptions();
    }
    if (changes['fields'] || changes['model']) {
      this.buildForm();
    }
  }

  private loadAllRelationOptions(): void {
    for (const field of this.formFields) {
      if (field.type !== 'relation-select' && field.type !== 'relation-multiselect') continue;
      if (!field.relationResourcePath) continue;
      this.loadRelationOptions(field);
    }
  }

  private loadRelationOptions(field: EntityFieldConfig): void {
    this.relationLoading[field.key] = true;
    const labelKey = field.relationLabelKey ?? 'name';
    const valueKey = field.relationValueKey ?? 'id';

    this.api
      .list<Record<string, unknown>>(field.relationResourcePath!, { page: 1, page_size: 200 })
      .subscribe({
        next: (res) => {
          this.relationOptions[field.key] = res.data.map((row) => ({
            label: String(row[labelKey] ?? row[valueKey]),
            value: String(row[valueKey]),
          }));
          this.relationLoading[field.key] = false;
        },
        error: () => {
          this.relationOptions[field.key] = [];
          this.relationLoading[field.key] = false;
        },
      });
  }

  private buildForm(): void {
    const group: Record<string, unknown> = {};
    for (const field of this.formFields) {
      const raw = this.model ? (this.model as Record<string, unknown>)[field.key] : undefined;
      const value = field.type === 'date' && typeof raw === 'string' ? new Date(raw) : raw ?? this.defaultFor(field);
      const validators = field.required ? [field.type === 'relation-multiselect' ? requiredArray : Validators.required] : [];
      group[field.key] = [{ value, disabled: false }, validators];
    }
    this.form = this.fb.group(group);
  }

  private defaultFor(field: EntityFieldConfig): unknown {
    if (field.type === 'boolean') return false;
    if (field.type === 'relation-multiselect') return [];
    return null;
  }

  submit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
    const payload: Record<string, unknown> = {};
    for (const field of this.formFields) {
      const value = raw[field.key];
      payload[field.key] = field.type === 'date' && value instanceof Date ? value.toISOString().slice(0, 10) : value;
    }
    this.save.emit(payload);
  }

  openQuickCreate(field: EntityFieldConfig): void {
    this.quickCreateField = field;
    this.quickCreateVisible = true;
  }

  onQuickCreateSave(payload: Record<string, unknown>): void {
    const field = this.quickCreateField;
    if (!field?.relationResourcePath) return;

    const labelKey = field.relationLabelKey ?? 'name';
    this.api.create<Record<string, unknown>>(field.relationResourcePath, payload).subscribe({
      next: (res) => {
        const created = res.data;
        const valueKey = field.relationValueKey ?? 'id';
        const newOption: SelectOption = { label: String(created[labelKey] ?? created[valueKey]), value: String(created[valueKey]) };

        this.relationOptions[field.key] = [...(this.relationOptions[field.key] || []), newOption];

        const control = this.form.get(field.key);
        if (control) {
          if (field.type === 'relation-multiselect') {
            const current = (control.value as string[]) || [];
            control.setValue([...current, newOption.value]);
          } else {
            control.setValue(newOption.value);
          }
          control.markAsDirty();
        }

        this.quickCreateVisible = false;
        this.quickCreateField = null;
      },
    });
  }
}
