import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AttachmentApiService, AttachmentRecord } from '../../core/api/attachment-api.service';

const PAGE_SIZE = 50;

/**
 * Read-only aggregator (same bespoke shape as warnings.component.ts) -- every
 * attachment across every module, in one grid. No cross-entity "all documents"
 * view existed before this; every attachment was only browsable filtered to one
 * (entity_type, entity_id). Not EntityPageComponent: creating an attachment needs
 * a file-upload control the generic form doesn't have, so this is view/download/
 * delete only -- uploads still happen from the record's own page.
 */
@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">All Documents</h2>
          <p class="panel__subtitle">Every attachment across every module, in one place.</p>
        </div>
        <div class="panel__control">
          <input type="text" placeholder="Search by document name…" [(ngModel)]="search" (ngModelChange)="onSearchChange()" />
        </div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <p class="panel__hint" *ngIf="!loading && rows.length === 0">No documents found.</p>

        <table class="report-table" *ngIf="!loading && rows.length > 0">
          <thead>
            <tr>
              <th>Document name</th>
              <th>Type</th>
              <th>Relation</th>
              <th>Uploaded</th>
              <th>Expiry</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let r of rows">
              <td>{{ r.document_name || r.original_filename }}</td>
              <td>{{ r.document_type || '--' }}</td>
              <td>{{ r.entity_type }}</td>
              <td>{{ r.created_at | slice: 0:10 }}</td>
              <td>{{ r.expiry_date || '--' }}</td>
              <td class="report-table__actions">
                <a [href]="fileUrl(r.id)" target="_blank" rel="noopener">Download</a>
                <button type="button" (click)="remove(r)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pager" *ngIf="!loading && (page > 1 || rows.length === pageSize)">
          <button type="button" [disabled]="page <= 1" (click)="goToPage(page - 1)">Previous</button>
          <span>Page {{ page }}</span>
          <button type="button" [disabled]="rows.length < pageSize" (click)="goToPage(page + 1)">Next</button>
        </div>
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
      .panel__control input {
        padding: 0.45rem 0.7rem;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-size: 0.85rem;
        min-width: 220px;
      }
      .panel__body {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        padding: 1.25rem 1.5rem;
      }
      .panel__hint {
        color: #64748b;
        font-size: 0.9rem;
      }
      .report-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
      }
      .report-table th {
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #64748b;
        border-bottom: 2px solid #e2e8f0;
        padding: 0.5rem 0.6rem;
      }
      .report-table td {
        padding: 0.5rem 0.6rem;
        border-bottom: 1px solid #f1f5f9;
        color: #0f172a;
      }
      .report-table__actions {
        display: flex;
        gap: 0.6rem;
        white-space: nowrap;
      }
      .report-table__actions a {
        color: #0f766e;
        font-weight: 600;
        text-decoration: none;
      }
      .report-table__actions a:hover {
        text-decoration: underline;
      }
      .report-table__actions button {
        border: none;
        background: none;
        color: #dc2626;
        font-weight: 600;
        cursor: pointer;
        padding: 0;
        font-size: 0.85rem;
      }
      .pager {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-top: 1rem;
        font-size: 0.85rem;
        color: #334155;
      }
      .pager button {
        padding: 0.3rem 0.7rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #fff;
        cursor: pointer;
      }
      .pager button:disabled {
        opacity: 0.5;
        cursor: default;
      }
    `,
  ],
})
export class DocumentsComponent implements OnInit {
  rows: AttachmentRecord[] = [];
  loading = false;
  search = '';
  page = 1;
  pageSize = PAGE_SIZE;

  constructor(private readonly api: AttachmentApiService) {}

  ngOnInit(): void {
    this.load();
  }

  onSearchChange(): void {
    this.page = 1;
    this.load();
  }

  goToPage(page: number): void {
    this.page = page;
    this.load();
  }

  fileUrl(id: string): string {
    return this.api.fileUrl(id);
  }

  remove(row: AttachmentRecord): void {
    if (!confirm(`Delete "${row.document_name || row.original_filename}"? This cannot be undone.`)) return;
    this.api.remove(row.id).subscribe(() => this.load());
  }

  private load(): void {
    this.loading = true;
    this.api.listAll(this.page, this.pageSize, this.search || undefined).subscribe({
      next: (res) => {
        this.rows = res.data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }
}
