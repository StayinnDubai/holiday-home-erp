import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePickerModule } from 'primeng/datepicker';
import { BalanceSheet, ReportsApiService } from '../../core/api/reports-api.service';
import { formatAmount } from '../../shared/utils/amount';
import { toLocalDateString } from '../../shared/utils/date';

/** Read-only report (bespoke component, not EntityPageComponent). Asset/liability/
 * equity accounts as of a date, plus a computed year-to-date "Current year result"
 * folded into equity so the sheet balances -- v1 has no period-close step that would
 * otherwise roll P&L into the seeded "3040 Current year result" account for real
 * (backend/app/services/reports.py). */
@Component({
  selector: 'app-balance-sheet',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePickerModule],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Balance Sheet</h2>
          <p class="panel__subtitle">Assets, liabilities and equity as of a date. Only posted journal entries count.</p>
        </div>
        <div class="panel__control">
          <label>As of</label>
          <p-datepicker [ngModel]="asOfDate" (ngModelChange)="onAsOfChange($event)" dateFormat="yy-mm-dd" />
        </div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <ng-container *ngIf="!loading && report">
          <h3 class="report-section">Assets</h3>
          <p class="panel__hint" *ngIf="report.asset_lines.length === 0">No posted asset activity yet.</p>
          <table class="report-table" *ngIf="report.asset_lines.length > 0">
            <tbody>
              <tr *ngFor="let l of report.asset_lines">
                <td>{{ l.account_code }}</td>
                <td>{{ l.account_name }}</td>
                <td class="report-table__num">{{ formatAmount(l.balance) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total assets</td>
                <td class="report-table__num">{{ formatAmount(report.total_assets) }}</td>
              </tr>
            </tfoot>
          </table>

          <h3 class="report-section">Liabilities</h3>
          <p class="panel__hint" *ngIf="report.liability_lines.length === 0">No posted liability activity yet.</p>
          <table class="report-table" *ngIf="report.liability_lines.length > 0">
            <tbody>
              <tr *ngFor="let l of report.liability_lines">
                <td>{{ l.account_code }}</td>
                <td>{{ l.account_name }}</td>
                <td class="report-table__num">{{ formatAmount(l.balance) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total liabilities</td>
                <td class="report-table__num">{{ formatAmount(report.total_liabilities) }}</td>
              </tr>
            </tfoot>
          </table>

          <h3 class="report-section">Equity</h3>
          <p class="panel__hint" *ngIf="report.equity_lines.length === 0">No posted equity activity yet.</p>
          <table class="report-table">
            <tbody *ngIf="report.equity_lines.length > 0">
              <tr *ngFor="let l of report.equity_lines">
                <td>{{ l.account_code }}</td>
                <td>{{ l.account_name }}</td>
                <td class="report-table__num">{{ formatAmount(l.balance) }}</td>
              </tr>
            </tbody>
            <tbody>
              <tr>
                <td colspan="2">Current year result (computed, YTD)</td>
                <td class="report-table__num">{{ formatAmount(report.current_year_result) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td colspan="2">Total equity</td>
                <td class="report-table__num">{{ formatAmount(report.total_equity + report.current_year_result) }}</td>
              </tr>
            </tfoot>
          </table>

          <div
            class="report-summary"
            [class.report-summary--positive]="isBalanced"
            [class.report-summary--negative]="!isBalanced"
          >
            Assets {{ formatAmount(report.total_assets) }} vs. Liabilities + Equity
            {{ formatAmount(report.total_liabilities + report.total_equity + report.current_year_result) }}
            -- {{ isBalanced ? 'balanced' : 'out of balance' }}
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
        font-size: 0.9rem;
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
export class BalanceSheetComponent implements OnInit {
  asOfDate = new Date();
  report: BalanceSheet | null = null;
  loading = false;
  formatAmount = formatAmount;

  constructor(private readonly api: ReportsApiService) {}

  ngOnInit(): void {
    this.load();
  }

  get isBalanced(): boolean {
    if (!this.report) return true;
    const rhs = this.report.total_liabilities + this.report.total_equity + this.report.current_year_result;
    return Math.abs(this.report.total_assets - rhs) < 0.005;
  }

  onAsOfChange(date: Date): void {
    this.asOfDate = date;
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.api.balanceSheet(toLocalDateString(this.asOfDate)).subscribe({
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
