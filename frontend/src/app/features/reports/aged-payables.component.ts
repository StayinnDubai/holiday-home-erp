import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { AgedPayables, ReportsApiService } from '../../core/api/reports-api.service';
import { formatAmount } from '../../shared/utils/amount';
import { toLocalDateString } from '../../shared/utils/date';

const BUCKETS = ['Current', '1-30', '31-60', '61-90', '90+'];

/**
 * Read-only report (bespoke component, same shape as trial-balance.component.ts).
 * Bills have no partial-payment tracking, so "outstanding" is binary -- see
 * backend/app/services/reports.py's aged_payables docstring for the bucketing rule.
 */
@Component({
  selector: 'app-aged-payables',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePickerModule],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Aged Payables</h2>
          <p class="panel__subtitle">Outstanding bills (recorded/scheduled/disputed), bucketed by days overdue.</p>
        </div>
        <div class="panel__control">
          <label>As of</label>
          <p-datepicker [ngModel]="asOfDate" (ngModelChange)="onAsOfChange($event)" dateFormat="yy-mm-dd" />
        </div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <p class="panel__hint" *ngIf="!loading && report && report.lines.length === 0">
          No outstanding bills as of this date.
        </p>

        <div class="bucket-totals" *ngIf="!loading && report">
          <div class="bucket-totals__item" *ngFor="let b of buckets">
            <div class="bucket-totals__label">{{ b }}</div>
            <div class="bucket-totals__value">{{ formatAmount(report.bucket_totals[b] || 0) }}</div>
          </div>
          <div class="bucket-totals__item bucket-totals__item--grand">
            <div class="bucket-totals__label">Grand total</div>
            <div class="bucket-totals__value">{{ formatAmount(report.grand_total) }}</div>
          </div>
        </div>

        <table class="report-table" *ngIf="!loading && report && report.lines.length > 0">
          <thead>
            <tr>
              <th>Bill number</th>
              <th>Supplier</th>
              <th>Due date</th>
              <th>Bucket</th>
              <th class="report-table__num">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let l of report.lines">
              <td>{{ l.bill_number }}</td>
              <td>{{ l.supplier_name }}</td>
              <td>{{ l.due_date || '--' }}</td>
              <td>{{ l.bucket }}</td>
              <td class="report-table__num">{{ formatAmount(l.amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="4">Total</td>
              <td class="report-table__num">{{ formatAmount(report.grand_total) }}</td>
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
      .bucket-totals {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(9rem, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.25rem;
      }
      .bucket-totals__item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
      }
      .bucket-totals__item--grand {
        background: #f0fdf4;
        border-color: #bbf7d0;
      }
      .bucket-totals__label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
      .bucket-totals__value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        font-variant-numeric: tabular-nums;
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
      .report-table tfoot td {
        font-weight: 700;
        border-top: 2px solid #e2e8f0;
        border-bottom: none;
      }
    `,
  ],
})
export class AgedPayablesComponent implements OnInit {
  asOfDate = new Date();
  report: AgedPayables | null = null;
  loading = false;
  buckets = BUCKETS;
  formatAmount = formatAmount;

  constructor(private readonly api: ReportsApiService) {}

  ngOnInit(): void {
    this.load();
  }

  onAsOfChange(date: Date): void {
    this.asOfDate = date;
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.api.agedPayables(toLocalDateString(this.asOfDate)).subscribe({
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
