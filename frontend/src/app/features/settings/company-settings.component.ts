import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DatePickerModule } from 'primeng/datepicker';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { CompanyApiService, CompanyRecord } from '../../core/api/company-api.service';
import { CrudApiService } from '../../core/api/crud-api.service';
import { AttachmentsFieldComponent } from '../../shared/crud/attachments-field.component';
import { AttachmentsListComponent } from '../../shared/crud/attachments-list.component';

interface CurrencyOption {
  id: string;
  name: string;
}

const MONTHS = [
  { label: 'January', value: 1 },
  { label: 'February', value: 2 },
  { label: 'March', value: 3 },
  { label: 'April', value: 4 },
  { label: 'May', value: 5 },
  { label: 'June', value: 6 },
  { label: 'July', value: 7 },
  { label: 'August', value: 8 },
  { label: 'September', value: 9 },
  { label: 'October', value: 10 },
  { label: 'November', value: 11 },
  { label: 'December', value: 12 },
];

/**
 * Settings > Company (doc §7): "legal entity, TRN, licence, logo, addresses,
 * financial year 1 January - 31 December inclusive (confirmed), base currency,
 * timezone" -- plus brand name, website, phone, VAT number, manager name, date of
 * registration and shareholders, requested directly. A single edit form bound
 * directly to the page, not a dialog over a grid -- deliberately not
 * EntityPageComponent/EntityFormComponent, since there is exactly one company
 * record (D-1) and never a list of them.
 *
 * Logo (AttachmentsFieldComponent, thumbnail gallery) and Documents
 * (AttachmentsListComponent, one row per document with view/edit/delete) both reuse
 * the generic attachments backend (doc §5.3) but under different entityType values
 * ('company' vs 'company_document') so the two lists never mix.
 */
@Component({
  selector: 'app-company-settings',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    DatePickerModule,
    InputTextModule,
    SelectModule,
    TextareaModule,
    AttachmentsFieldComponent,
    AttachmentsListComponent,
  ],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Company</h2>
          <p class="panel__subtitle">Legal entity profile and identifiers (doc §7).</p>
        </div>
      </div>

      <form *ngIf="company" [formGroup]="form" (ngSubmit)="save()" class="panel__body">
        <div class="field-row">
          <div class="field">
            <label for="legal_name">Legal name<span class="req">*</span></label>
            <input id="legal_name" pInputText formControlName="legal_name" />
          </div>
          <div class="field">
            <label for="brand_name">Brand name</label>
            <input id="brand_name" pInputText formControlName="brand_name" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label for="trn">TRN</label>
            <input id="trn" pInputText formControlName="trn" />
          </div>
          <div class="field">
            <label for="vat_number">VAT number</label>
            <input id="vat_number" pInputText formControlName="vat_number" />
          </div>
          <div class="field">
            <label for="license_number">Licence number</label>
            <input id="license_number" pInputText formControlName="license_number" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label for="website">Website</label>
            <input id="website" pInputText formControlName="website" />
          </div>
          <div class="field">
            <label for="phone_number">Phone number</label>
            <input id="phone_number" pInputText formControlName="phone_number" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label for="manager_name">Manager name</label>
            <input id="manager_name" pInputText formControlName="manager_name" />
          </div>
          <div class="field">
            <label for="date_of_registration">Date of registration</label>
            <p-datepicker inputId="date_of_registration" formControlName="date_of_registration" dateFormat="yy-mm-dd" />
          </div>
        </div>

        <div class="field">
          <label for="address">Address</label>
          <textarea id="address" pTextarea formControlName="address" rows="3"></textarea>
        </div>

        <div class="field">
          <label for="shareholders">Shareholders</label>
          <textarea id="shareholders" pTextarea formControlName="shareholders" rows="3" placeholder="One per line"></textarea>
        </div>

        <div class="field">
          <label>Logo</label>
          <app-attachments-field entityType="company" [entityId]="company.id" />
        </div>

        <div class="field-row">
          <div class="field">
            <label for="financial_year_start_month">Financial year starts</label>
            <p-select
              inputId="financial_year_start_month"
              formControlName="financial_year_start_month"
              [options]="months"
              optionLabel="label"
              optionValue="value"
            />
          </div>
          <div class="field">
            <label for="base_currency_id">Base currency</label>
            <p-select
              inputId="base_currency_id"
              formControlName="base_currency_id"
              [options]="currencies"
              optionLabel="name"
              optionValue="id"
              placeholder="Select..."
            />
          </div>
          <div class="field">
            <label for="timezone">Timezone</label>
            <input id="timezone" pInputText formControlName="timezone" />
          </div>
        </div>

        <div class="panel__actions">
          <span class="saved-note" *ngIf="savedAt">Saved.</span>
          <p-button label="Save" icon="pi pi-check" type="submit" [disabled]="form.invalid || saving" [loading]="saving" />
        </div>
      </form>

      <p *ngIf="!company && !loadError" class="panel__hint">Loading...</p>
      <p *ngIf="loadError" class="panel__hint panel__hint--error">{{ loadError }}</p>
    </div>

    <div class="panel panel--documents" *ngIf="company">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Documents</h2>
          <p class="panel__subtitle">Manually attached company documents (doc §5.3) -- trade licence, MOA, etc.</p>
        </div>
      </div>
      <div class="panel__body">
        <app-attachments-list entityType="company_document" [entityId]="company.id" />
      </div>
    </div>
  `,
  styles: [
    `
      .panel {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
      }
      .panel--documents {
        margin-top: 1.5rem;
      }
      .panel__header {
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid #e2e8f0;
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
      .panel__body {
        display: flex;
        flex-direction: column;
        gap: 1.1rem;
        padding: 1.5rem;
        max-width: 40rem;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        flex: 1;
      }
      .field-row {
        display: flex;
        gap: 1rem;
      }
      .field label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
      }
      .field .req {
        color: #dc2626;
        margin-left: 0.15rem;
      }
      .field input[pInputText],
      .field p-select,
      .field p-datepicker,
      .field textarea {
        width: 100%;
      }
      .panel__actions {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.75rem;
        margin-top: 0.5rem;
      }
      .saved-note {
        color: #16a34a;
        font-size: 0.85rem;
      }
      .panel__hint {
        padding: 1.5rem;
        color: #64748b;
      }
      .panel__hint--error {
        color: #dc2626;
      }
    `,
  ],
})
export class CompanySettingsComponent implements OnInit {
  months = MONTHS;
  currencies: CurrencyOption[] = [];
  company: CompanyRecord | null = null;
  form: FormGroup;
  saving = false;
  savedAt: Date | null = null;
  loadError: string | null = null;

  constructor(
    private readonly fb: FormBuilder,
    private readonly api: CompanyApiService,
    private readonly crudApi: CrudApiService
  ) {
    this.form = this.fb.group({
      legal_name: ['', Validators.required],
      brand_name: [''],
      trn: [''],
      vat_number: [''],
      license_number: [''],
      website: [''],
      phone_number: [''],
      manager_name: [''],
      date_of_registration: [null as Date | null],
      shareholders: [''],
      address: [''],
      financial_year_start_month: [1],
      base_currency_id: [null as string | null],
      timezone: ['Asia/Dubai'],
    });
  }

  ngOnInit(): void {
    this.crudApi.list<CurrencyOption>('currencies', { page: 1, page_size: 200 }).subscribe({
      next: (res) => (this.currencies = res.data),
    });

    this.api.get().subscribe({
      next: (res) => {
        this.company = res.data;
        this.form.patchValue({
          ...res.data,
          date_of_registration: res.data.date_of_registration ? new Date(res.data.date_of_registration) : null,
        });
      },
      error: () => {
        this.loadError = 'Could not load the company record. Has the seed script been run (python -m app.seed.run)?';
      },
    });
  }

  save(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.savedAt = null;

    const raw = this.form.getRawValue();
    const payload = {
      ...raw,
      date_of_registration: raw.date_of_registration instanceof Date ? raw.date_of_registration.toISOString().slice(0, 10) : null,
    };

    this.api.update(payload).subscribe({
      next: (res) => {
        this.company = res.data;
        this.saving = false;
        this.savedAt = new Date();
      },
      error: () => {
        this.saving = false;
      },
    });
  }
}
