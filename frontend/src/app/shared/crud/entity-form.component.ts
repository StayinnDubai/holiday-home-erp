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
import { AttachmentsFieldComponent } from './attachments-field.component';
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
    AttachmentsFieldComponent,
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

        <div *ngIf="field.type === 'action-date'" class="entity-form__action-date">
          <div class="entity-form__action-date-buttons">
            <p-button
              label="Set manually"
              size="small"
              type="button"
              [outlined]="dateSource(field) !== 'manual'"
              (onClick)="setDateSource(field, 'manual')"
            />
            <p-button
              label="Reconcile from bank statement"
              size="small"
              type="button"
              [outlined]="dateSource(field) !== 'bank_reconciliation'"
              (onClick)="setDateSource(field, 'bank_reconciliation')"
            />
          </div>
          <p-datepicker
            [inputId]="field.key"
            [formControlName]="field.key"
            dateFormat="yy-mm-dd"
            (onSelect)="ensureDateSource(field)"
            placeholder="Pick a date..."
          />
        </div>

        <div *ngIf="field.type === 'attachments'">
          <app-attachments-field
            *ngIf="modelId; else attachmentsUnsaved"
            [entityType]="field.attachmentEntityType || ''"
            [entityId]="modelId"
          />
          <ng-template #attachmentsUnsaved>
            <p class="entity-form__hint">Save the record first, then reopen it to attach a file.</p>
          </ng-template>
        </div>
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
      .entity-form__action-date {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
      }
      .entity-form__action-date-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
      }
      .entity-form__hint {
        margin: 0;
        color: #64748b;
        font-size: 0.85rem;
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

  /** String id of the record being edited, or '' for a new/unsaved record --
   * 'attachments' fields need this to know whether they have anything to attach to. */
  get modelId(): string {
    return this.model ? String((this.model as Record<string, unknown>)['id'] ?? '') : '';
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
      const isDateLike = field.type === 'date' || field.type === 'action-date';
      const value = isDateLike && typeof raw === 'string' ? new Date(raw) : raw ?? this.defaultFor(field);
      const validators = field.required ? [field.type === 'relation-multiselect' ? requiredArray : Validators.required] : [];
      group[field.key] = [{ value, disabled: false }, validators];

      // 'action-date' fields write to a sibling "how was this set" field that isn't
      // necessarily its own entry in `fields` (it usually only needs to exist as a
      // grid column, not a rendered form field) -- give it a control here so there's
      // somewhere for setDateSource()/ensureDateSource() to write.
      if (field.type === 'action-date' && field.sourceFieldKey && !group[field.sourceFieldKey]) {
        const sourceRaw = this.model ? (this.model as Record<string, unknown>)[field.sourceFieldKey] : undefined;
        group[field.sourceFieldKey] = [sourceRaw ?? null];
      }
    }
    this.form = this.fb.group(group);
  }

  dateSource(field: EntityFieldConfig): unknown {
    return field.sourceFieldKey ? this.form.get(field.sourceFieldKey)?.value : null;
  }

  setDateSource(field: EntityFieldConfig, source: 'manual' | 'bank_reconciliation'): void {
    if (!field.sourceFieldKey) return;
    this.form.get(field.sourceFieldKey)?.setValue(source);
    this.form.get(field.sourceFieldKey)?.markAsDirty();
  }

  /** Picking a date without ever clicking one of the two source buttons still needs
   * a source recorded -- defaults to 'manual', since that's what typing/picking a
   * date directly is. */
  ensureDateSource(field: EntityFieldConfig): void {
    if (!field.sourceFieldKey) return;
    const control = this.form.get(field.sourceFieldKey);
    if (control && !control.value) control.setValue('manual');
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
      const isDateLike = field.type === 'date' || field.type === 'action-date';
      payload[field.key] = isDateLike && value instanceof Date ? value.toISOString().slice(0, 10) : value;

      if (field.type === 'action-date' && field.sourceFieldKey) {
        payload[field.sourceFieldKey] = raw[field.sourceFieldKey] ?? null;
      }
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
