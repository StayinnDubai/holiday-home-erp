import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { ChequePosition, ReportsApiService } from '../../core/api/reports-api.service';
import { formatAmount } from '../../shared/utils/amount';
import { toLocalDateString } from '../../shared/utils/date';

/**
 * Read-only report (bespoke component, same shape as trial-balance.component.ts).
 * No date-bucketing needed -- the `status` field already *is* the position, so this
 * is just a group-by-(direction, status) as of a date.
 */
@Component({
  selector: 'app-cheque-position',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePickerModule],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Cheque Position</h2>
          <p class="panel__subtitle">Cheques grouped by direction and status, as of a date.</p>
        </div>
        <div class="panel__control">
          <label>As of</label>
          <p-datepicker [ngModel]="asOfDate" (ngModelChange)="onAsOfChange($event)" dateFormat="yy-mm-dd" />
        </div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <p class="panel__hint" *ngIf="!loading && report && report.groups.length === 0">
          No cheques as of this date.
        </p>

        <table class="report-table" *ngIf="!loading && report && report.groups.length > 0">
          <thead>
            <tr>
              <th>Direction</th>
              <th>Status</th>
              <th class="report-table__num">Count</th>
              <th class="report-table__num">Total amount</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let g of report.groups">
              <td class="report-table__type">{{ g.direction }}</td>
              <td class="report-table__type">{{ g.status }}</td>
              <td class="report-table__num">{{ g.count }}</td>
              <td class="report-table__num">{{ formatAmount(g.total_amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2">Total</td>
              <td class="report-table__num">{{ totalCount }}</td>
              <td class="report-table__num">{{ formatAmount(totalAmount) }}</td>
            </tr>
          </tfoot>
        </table>
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
      .panel__control {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .panel__control label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
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
      .report-table__num {
        text-align: right;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
      }
      .report-table__type {
        text-transform: capitalize;
        color: #0f172a;
      }
      .report-table tfoot td {
        font-weight: 700;
        border-top: 2px solid #e2e8f0;
        border-bottom: none;
      }
    `,
  ],
})
export class ChequePositionComponent implements OnInit {
  asOfDate = new Date();
  report: ChequePosition | null = null;
  loading = false;
  formatAmount = formatAmount;

  constructor(private readonly api: ReportsApiService) {}

  ngOnInit(): void {
    this.load();
  }

  onAsOfChange(date: Date): void {
    this.asOfDate = date;
    this.load();
  }

  get totalCount(): number {
    return this.report?.groups.reduce((sum, g) => sum + g.count, 0) ?? 0;
  }

  get totalAmount(): number {
    return this.report?.groups.reduce((sum, g) => sum + g.total_amount, 0) ?? 0;
  }

  private load(): void {
    this.loading = true;
    this.api.chequePosition(toLocalDateString(this.asOfDate)).subscribe({
      next: (res) => {
        this.report = res;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }
}
