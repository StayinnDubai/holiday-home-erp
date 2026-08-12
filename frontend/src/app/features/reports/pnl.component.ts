import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { Pnl, ReportsApiService } from '../../core/api/reports-api.service';
import { formatAmount } from '../../shared/utils/amount';
import { toLocalDateString } from '../../shared/utils/date';

/** Read-only report (bespoke component, not EntityPageComponent) -- revenue minus cost
 * for posted journal entries within a date range (backend/app/services/reports.py). */
@Component({
  selector: 'app-pnl',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePickerModule],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Profit &amp; Loss</h2>
          <p class="panel__subtitle">Revenue and cost accounts for posted journal entries within the period.</p>
        </div>
        <div class="panel__controls">
          <div class="panel__control">
            <label>From</label>
            <p-datepicker [ngModel]="dateFrom" (ngModelChange)="onDateFromChange($event)" dateFormat="yy-mm-dd" />
          </div>
          <div class="panel__control">
            <label>To</label>
            <p-datepicker [ngModel]="dateTo" (ngModelChange)="onDateToChange($event)" dateFormat="yy-mm-dd" />
          </div>
        </div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <ng-container *ngIf="!loading && report">
          <h3 class="report-section">Revenue</h3>
          <p class="panel__hint" *ngIf="report.revenue_lines.length === 0">No posted revenue in this period.</p>
          <table class="report-table" *ngIf="report.revenue_lines.length > 0">
            <thead>
              <tr>
                <th>Code</th>
                <th>Account</th>
                <th class="report-table__num">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let l of report.revenue_lines">
                <td>{{ l.account_code }}</td>
                <td>{{ l.account_name }}</td>
                <td class="report-table__num">{{ formatAmount(l.balance) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total revenue</td>
                <td class="report-table__num">{{ formatAmount(report.total_revenue) }}</td>
              </tr>
            </tfoot>
          </table>

          <h3 class="report-section">Cost</h3>
          <p class="panel__hint" *ngIf="report.cost_lines.length === 0">No posted cost in this period.</p>
          <table class="report-table" *ngIf="report.cost_lines.length > 0">
            <thead>
              <tr>
                <th>Code</th>
                <th>Account</th>
                <th class="report-table__num">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let l of report.cost_lines">
                <td>{{ l.account_code }}</td>
                <td>{{ l.account_name }}</td>
                <td class="report-table__num">{{ formatAmount(l.balance) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total cost</td>
                <td class="report-table__num">{{ formatAmount(report.total_cost) }}</td>
              </tr>
            </tfoot>
          </table>

          <div class="report-summary" [class.report-summary--positive]="report.net_income >= 0" [class.report-summary--negative]="report.net_income < 0">
            Net income: {{ formatAmount(report.net_income) }}
          </div>
        </ng-container>
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
      .panel__controls {
        display: flex;
        gap: 1rem;
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
      .report-section {
        margin: 1.25rem 0 0.5rem;
        font-size: 0.85rem;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
      .report-section:first-child {
        margin-top: 0;
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
      .report-summary {
        margin-top: 1.5rem;
        padding: 0.85rem 1rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
      }
      .report-summary--positive {
        background: #f0fdf4;
        color: #166534;
      }
      .report-summary--negative {
        background: #fef2f2;
        color: #b91c1c;
      }
    `,
  ],
})
export class PnlComponent implements OnInit {
  dateFrom = new Date(new Date().getFullYear(), 0, 1);
  dateTo = new Date();
  report: Pnl | null = null;
  loading = false;
  formatAmount = formatAmount;

  constructor(private readonly api: ReportsApiService) {}

  ngOnInit(): void {
    this.load();
  }

  onDateFromChange(date: Date): void {
    this.dateFrom = date;
    this.load();
  }

  onDateToChange(date: Date): void {
    this.dateTo = date;
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.api.pnl(toLocalDateString(this.dateFrom), toLocalDateString(this.dateTo)).subscribe({
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
