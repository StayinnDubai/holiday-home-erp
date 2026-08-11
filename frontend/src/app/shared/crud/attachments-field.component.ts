import { CommonModule } from '@angular/common';
import { Component, ElementRef, Input, OnChanges, SimpleChanges, ViewChild } from '@angular/core';
import { ButtonModule } from 'primeng/button';
import { AttachmentApiService, AttachmentRecord } from '../../core/api/attachment-api.service';

/**
 * Small upload/gallery panel for a single entity's attachments (doc §5.3), used by
 * entity-form's 'attachments' field type (e.g. a cheque's photo). Generic on
 * `entityType` so any module can reuse it the same way relation-select fields reuse
 * CrudApiService -- not cheque-specific, just first wired up there.
 *
 * Needs a real `entityId` to call the API against, so it only renders once the
 * parent record has been saved at least once -- entity-form.component hides this
 * field entirely for brand-new (unsaved) records and shows a placeholder instead.
 */
@Component({
  selector: 'app-attachments-field',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  template: `
    <div class="attachments-field">
      <div class="attachments-field__list" *ngIf="attachments.length">
        <div class="attachments-field__item" *ngFor="let a of attachments">
          <a [href]="api.fileUrl(a.id)" target="_blank" rel="noopener">
            <img
              *ngIf="isImage(a)"
              [src]="api.fileUrl(a.id)"
              [alt]="a.original_filename"
              class="attachments-field__thumb"
            />
            <span *ngIf="!isImage(a)" class="attachments-field__file">
              <i class="pi pi-file"></i>
              {{ a.original_filename }}
            </span>
          </a>
          <button type="button" class="attachments-field__remove" title="Delete" (click)="remove(a)">
            <i class="pi pi-times"></i>
          </button>
        </div>
      </div>

      <p class="attachments-field__empty" *ngIf="!attachments.length && !loading">No files uploaded yet.</p>

      <input
        #fileInput
        type="file"
        accept="image/*,application/pdf"
        hidden
        (change)="onFileSelected($event)"
      />
      <p-button label="Upload photo" icon="pi pi-upload" size="small" [text]="true" type="button" [loading]="uploading" (onClick)="fileInput.click()" />
    </div>
  `,
  styles: [
    `
      .attachments-field {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
      }
      .attachments-field__list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
      }
      .attachments-field__item {
        position: relative;
        width: 5.5rem;
      }
      .attachments-field__thumb {
        width: 5.5rem;
        height: 5.5rem;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        display: block;
      }
      .attachments-field__file {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        width: 5.5rem;
        height: 5.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-size: 0.7rem;
        text-align: center;
        overflow: hidden;
        padding: 0.25rem;
        color: #334155;
      }
      .attachments-field__remove {
        position: absolute;
        top: -0.4rem;
        right: -0.4rem;
        width: 1.25rem;
        height: 1.25rem;
        border-radius: 999px;
        border: none;
        background: #dc2626;
        color: #fff;
        font-size: 0.6rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .attachments-field__empty {
        margin: 0;
        color: #64748b;
        font-size: 0.85rem;
      }
    `,
  ],
})
export class AttachmentsFieldComponent implements OnChanges {
  @Input({ required: true }) entityType!: string;
  @Input({ required: true }) entityId!: string;

  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;

  attachments: AttachmentRecord[] = [];
  loading = false;
  uploading = false;

  constructor(readonly api: AttachmentApiService) {}

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

  isImage(a: AttachmentRecord): boolean {
    return !!a.content_type?.startsWith('image/');
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

  remove(a: AttachmentRecord): void {
    this.api.remove(a.id).subscribe({
      next: () => this.refresh(),
    });
  }
}
