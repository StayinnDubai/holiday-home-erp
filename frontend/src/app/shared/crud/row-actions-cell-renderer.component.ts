import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import type { ICellRendererAngularComp } from 'ag-grid-angular';
import type { ICellRendererParams } from 'ag-grid-community';
import { ButtonModule } from 'primeng/button';

/** ag-Grid context passed in from EntityPageComponent (via [context] on the grid). */
export interface RowActionsContext<T> {
  onEdit: (row: T) => void;
  onDelete: (row: T) => void;
}

/**
 * Edit/Delete buttons for every row in every module's grid (shared/crud). ag-Grid cell
 * renderers must be plain components implementing ICellRendererAngularComp -- this is
 * the one instance of that pattern, reused by every EntityPageComponent grid.
 *
 * ag-Grid's Infinite Row Model renders placeholder rows (params.data === undefined)
 * before the real page of data arrives -- without the `*ngIf="params?.data"` guard this
 * showed live, clickable Edit/Delete buttons on empty/loading rows that pointed at no
 * actual record.
 */
@Component({
  selector: 'app-row-actions-cell',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  template: `
    <div class="row-actions" *ngIf="params?.data">
      <p-button icon="pi pi-pencil" [text]="true" size="small" (onClick)="onEdit()" />
      <p-button icon="pi pi-trash" [text]="true" size="small" severity="danger" (onClick)="onDelete()" />
    </div>
  `,
  styles: [
    `
      .row-actions {
        display: flex;
        gap: 0.25rem;
        align-items: center;
        height: 100%;
      }
    `,
  ],
})
export class RowActionsCellRendererComponent implements ICellRendererAngularComp {
  params!: ICellRendererParams;

  agInit(params: ICellRendererParams): void {
    this.params = params;
  }

  refresh(params: ICellRendererParams): boolean {
    this.params = params;
    return true;
  }

  onEdit(): void {
    (this.params.context as RowActionsContext<unknown>)?.onEdit?.(this.params.data);
  }

  onDelete(): void {
    (this.params.context as RowActionsContext<unknown>)?.onDelete?.(this.params.data);
  }
}
