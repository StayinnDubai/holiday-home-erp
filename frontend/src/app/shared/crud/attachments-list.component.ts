import { CommonModule } from '@angular/common';
import { Component, ElementRef, Input, OnChanges, SimpleChanges, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ConfirmationService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { AttachmentApiService, AttachmentRecord } from '../../core/api/attachment-api.service';

/**
 * "Attach a document, see one line per document (name + attachment date), view/
 * edit/delete" -- a list-style counterpart to AttachmentsFieldComponent's thumbnail
 * gallery (used for e.g. a cheque photo or the company logo). Same generic
 * attachments backend (doc §5.3), different presentation: a row-per-document table
 * rather than a small image grid, because a document list is read by name, not by
 * thumbnail, and needs edit (rename) as a first-class action.
 *
 * Generic on `entityType` so it isn't Company-specific, even though Company's
 * "Documents" section is what asked for it -- pass a distinct entityType from
 * whatever else attaches to the same entityId (e.g. 'company_document' vs the
 * company logo's 'company') so the two lists don't mix.
 */
@Component({
  selector: 'app-attachments-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ButtonModule, ConfirmDialogModule, DialogModule, InputTextModule],
  providers: [ConfirmationService],
  template: `
    <div class="attachments-list">
      <table class="attachments-list__table" *ngIf="attachments.length">
        <thead>
          <tr>
            <th>Name</th>
            <th>Attached</th>
            <th class="attachments-list__actions-col"></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let a of attachments">
            <td>{{ a.document_name || a.original_filename }}</td>
            <td>{{ a.created_at | slice: 0:10 }}</td>
            <td class="attachments-list__actions">
              <button type="button" title="View" (click)="view(a)"><i class="pi pi-eye"></i></button>
              <button type="button" title="Edit" (click)="openEdit(a)"><i class="pi pi-pencil"></i></button>
              <button type="button" title="Delete" (click)="confirmDelete(a)"><i class="pi pi-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="attachments-list__empty" *ngIf="!attachments.length && !loading">No documents attached yet.</p>

      <input #fileInput type="file" accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx" hidden (change)="onFileSelected($event)" />
      <p-button label="Attach document" icon="pi pi-paperclip" size="small" [text]="true" type="button" [loading]="uploading" (onClick)="fileInput.click()" />
    </div>

    <p-dialog header="Edit document" [(visible)]="editVisible" [modal]="true" [dismissableMask]="true" [style]="{ width: '24rem' }">
      <form *ngIf="editForm" [formGroup]="editForm" (ngSubmit)="saveEdit()" class="attachments-list__edit-form">
        <label for="document_name">Name</label>
        <input id="document_name" pInputText formControlName="document_name" />
        <div class="attachments-list__edit-actions">
          <p-button label="Cancel" severity="secondary" [text]="true" type="button" (onClick)="editVisible = false" />
          <p-button label="Save" icon="pi pi-check" type="submit" [disabled]="editForm.invalid" />
        </div>
      </form>
    </p-dialog>

    <p-confirmDialog [style]="{ width: '26rem' }" icon="pi pi-exclamation-triangle" />
  `,
  styles: [
    `
      .attachments-list {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }
      .attachments-list__table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
      }
      .attachments-list__table th {
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #64748b;
        border-bottom: 1px solid #e2e8f0;
        padding: 0.5rem 0.5rem;
      }
      .attachments-list__table td {
        padding: 0.5rem 0.5rem;
        border-bottom: 1px solid #f1f5f9;
        color: #0f172a;
      }
      .attachments-list__actions-col {
        width: 6rem;
      }
      .attachments-list__actions {
        display: flex;
        gap: 0.4rem;
      }
      .attachments-list__actions button {
        border: none;
        background: transparent;
        color: #64748b;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 6px;
      }
      .attachments-list__actions button:hover {
        background: #f1f5f9;
        color: #0f172a;
      }
      .attachments-list__empty {
        margin: 0;
        color: #64748b;
        font-size: 0.85rem;
      }
      .attachments-list__edit-form {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      .attachments-list__edit-form label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
      }
      .attachments-list__edit-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
      }
    `,
  ],
})
export class AttachmentsListComponent implements OnChanges {
  @Input({ required: true }) entityType!: string;
  @Input({ required: true }) entityId!: string;

  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;

  attachments: AttachmentRecord[] = [];
  loading = false;
  uploading = false;

  editVisible = false;
  editForm: FormGroup | null = null;
  private editing: AttachmentRecord | null = null;

  constructor(
    private readonly api: AttachmentApiService,
    private readonly fb: FormBuilder,
    private readonly confirmationService: ConfirmationService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entityId'] && this.entityId) {
      this.refresh();
    }
  }

  private refresh(): void {
    this.loading = true;
    this.api.list(this.entityType, this.entityId).subscribe({
      next: (res) => {
        this.attachments = res.data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.uploading = true;
    this.api.upload(this.entityType, this.entityId, file).subscribe({
      next: () => {
        this.uploading = false;
        input.value = '';
        this.refresh();
      },
      error: () => {
        this.uploading = false;
        input.value = '';
      },
    });
  }

  view(a: AttachmentRecord): void {
    window.open(this.api.fileUrl(a.id), '_blank', 'noopener');
  }

  openEdit(a: AttachmentRecord): void {
    this.editing = a;
    this.editForm = this.fb.group({
      document_name: [a.document_name || a.original_filename, Validators.required],
    });
    this.editVisible = true;
  }

  saveEdit(): void {
    if (!this.editing || !this.editForm || this.editForm.invalid) return;
    this.api.update(this.editing.id, { document_name: this.editForm.value.document_name }).subscribe({
      next: () => {
        this.editVisible = false;
        this.editing = null;
        this.refresh();
      },
    });
  }

  confirmDelete(a: AttachmentRecord): void {
    this.confirmationService.confirm({
      header: 'Delete document',
      message: `Are you sure you want to delete "${a.document_name || a.original_filename}"? This cannot be undone.`,
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', text: true },
      accept: () => {
        this.api.remove(a.id).subscribe({
          next: () => this.refresh(),
        });
      },
    });
  }
}
