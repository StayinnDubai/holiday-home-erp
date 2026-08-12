import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { CrudApiService } from '../../core/api/crud-api.service';
import { ReportsApiService } from '../../core/api/reports-api.service';
import { WarningsApiService } from '../../core/api/warnings-api.service';
import { formatAmount } from '../../shared/utils/amount';
import { toLocalDateString } from '../../shared/utils/date';

interface InventoryItemRow {
  id: string;
  code: string;
  name: string;
  quantity_on_hand: number;
}

interface ChequeRow {
  id: string;
  cheque_number: string;
  direction: string;
  amount: number;
  cheque_date: string | null;
  counterparty_name: string | null;
}

const LOW_STOCK_THRESHOLD = 5;
const CHEQUES_DUE_WINDOW_DAYS = 14;
const CONTRACT_EXPIRING_WINDOW_DAYS = 30;
const CASH_ACCOUNT_CODES = new Set(['1010', '1020']);

function statusOrFilter(values: string[]): Record<string, unknown> {
  return {
    filterType: 'text',
    operator: 'OR',
    conditions: values.map((v) => ({ filterType: 'text', type: 'equals', filter: v })),
  };
}

function dateLessThanFilter(cutoff: string): Record<string, unknown> {
  return { filterType: 'date', type: 'lessThan', dateFrom: cutoff };
}

/**
 * Role-aware landing page (doc §5.11) -- tiles reuse endpoints that already exist
 * and work (the route was left as a placeholder until real modules/reports existed
 * to build tiles from; both now do). Bespoke component like company-settings.
 * component.ts, not EntityPageComponent -- this is a read-only summary, not a CRUD grid.
 */
@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="dashboard">
      <div class="tile" [class.tile--warn]="!balanced">
        <div class="tile__label">Trial balance</div>
        <div class="tile__value">{{ balanced ? 'Balanced' : 'Out of balance' }}</div>
        <div class="tile__sub">Dr {{ formatAmount(totalDebit) }} / Cr {{ formatAmount(totalCredit) }}</div>
        <a class="tile__link" routerLink="/accounting/trial-balance">View report</a>
      </div>

      <div class="tile" [class.tile--warn]="netIncome < 0">
        <div class="tile__label">Net income (YTD)</div>
        <div class="tile__value">{{ formatAmount(netIncome) }}</div>
        <div class="tile__sub">Year to date</div>
        <a class="tile__link" routerLink="/reports/pnl">View P&amp;L</a>
      </div>

      <div class="tile">
        <div class="tile__label">Cash position</div>
        <div class="tile__value">{{ formatAmount(cashPosition) }}</div>
        <div class="tile__sub">Bank + cash accounts (1010/1020)</div>
        <a class="tile__link" routerLink="/reports/balance-sheet">View balance sheet</a>
      </div>

      <div class="tile">
        <div class="tile__label">Active tenancy contracts</div>
        <div class="tile__value">{{ activeContracts }}</div>
        <div class="tile__sub">{{ expiringContracts }} expiring within {{ contractWindowDays }} days</div>
        <a class="tile__link" routerLink="/contracts/tenancy">View contracts</a>
      </div>

      <div class="tile" [class.tile--warn]="chequesDueSoon.length > 0">
        <div class="tile__label">Cheques due soon</div>
        <div class="tile__value">{{ chequesDueSoon.length }}</div>
        <ul class="tile__list" *ngIf="chequesDueSoon.length > 0">
          <li *ngFor="let c of chequesDueSoon.slice(0, 4)">
            {{ c.cheque_number }} -- {{ formatAmount(c.amount) }} ({{ c.cheque_date }})
          </li>
        </ul>
        <a class="tile__link" routerLink="/accounting/cheque-ledger">View cheque ledger</a>
      </div>

      <div class="tile" [class.tile--warn]="lowStockItems.length > 0">
        <div class="tile__label">Low stock inventory</div>
        <div class="tile__value">{{ lowStockItems.length }}</div>
        <ul class="tile__list" *ngIf="lowStockItems.length > 0">
          <li *ngFor="let i of lowStockItems.slice(0, 4)">{{ i.code }} -- {{ i.name }} ({{ i.quantity_on_hand }})</li>
        </ul>
        <a class="tile__link" routerLink="/accounting/inventory-items">View inventory</a>
      </div>

      <div class="tile">
        <div class="tile__label">Portfolio</div>
        <div class="tile__value">{{ buildingCount }} buildings</div>
        <div class="tile__sub">{{ unitCount }} units</div>
        <a class="tile__link" routerLink="/buildings">View buildings</a>
      </div>

      <div class="tile" [class.tile--warn]="warningCount > 0">
        <div class="tile__label">Warnings</div>
        <div class="tile__value">{{ warningCount }}</div>
        <div class="tile__sub">Overdue bills/invoices, bounced cheques, variances, and more</div>
        <a class="tile__link" routerLink="/reports/compliance-dashboard">View warnings</a>
      </div>
    </div>
  `,
  styles: [
    `
      .dashboard {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
        gap: 1rem;
      }
      .tile {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .tile--warn {
        border-color: #fde68a;
        background: #fffbeb;
      }
      .tile__label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
      .tile__value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
      }
      .tile__sub {
        font-size: 0.85rem;
        color: #64748b;
      }
      .tile__list {
        margin: 0.25rem 0 0;
        padding: 0 0 0 1rem;
        font-size: 0.8rem;
        color: #475569;
      }
      .tile__link {
        margin-top: 0.5rem;
        font-size: 0.82rem;
        color: #0f766e;
        font-weight: 600;
        text-decoration: none;
      }
      .tile__link:hover {
        text-decoration: underline;
      }
    `,
  ],
})
export class DashboardComponent implements OnInit {
  formatAmount = formatAmount;
  contractWindowDays = CONTRACT_EXPIRING_WINDOW_DAYS;

  balanced = true;
  totalDebit = 0;
  totalCredit = 0;
  netIncome = 0;
  cashPosition = 0;
  activeContracts = 0;
  expiringContracts = 0;
  chequesDueSoon: ChequeRow[] = [];
  lowStockItems: InventoryItemRow[] = [];
  buildingCount = 0;
  unitCount = 0;
  warningCount = 0;

  constructor(
    private readonly api: CrudApiService,
    private readonly reportsApi: ReportsApiService,
    private readonly warningsApi: WarningsApiService
  ) {}

  ngOnInit(): void {
    const today = toLocalDateString(new Date());
    const chequesDueCutoff = toLocalDateString(new Date(Date.now() + (CHEQUES_DUE_WINDOW_DAYS + 1) * 86400000));
    const contractsExpiringCutoff = toLocalDateString(
      new Date(Date.now() + (CONTRACT_EXPIRING_WINDOW_DAYS + 1) * 86400000)
    );

    forkJoin({
      trialBalance: this.reportsApi.trialBalance(today),
      balanceSheet: this.reportsApi.balanceSheet(today),
      activeContracts: this.api.list('tenancy-contracts', {
        page: 1,
        page_size: 1,
        filter_model: JSON.stringify({ status: { filterType: 'text', type: 'equals', filter: 'active' } }),
      }),
      expiringContracts: this.api.list('tenancy-contracts', {
        page: 1,
        page_size: 1,
        filter_model: JSON.stringify({
          status: { filterType: 'text', type: 'equals', filter: 'active' },
          end_date: dateLessThanFilter(contractsExpiringCutoff),
        }),
      }),
      chequesDue: this.api.list<ChequeRow>('cheques', {
        page: 1,
        page_size: 10,
        sort_by: 'cheque_date',
        sort_dir: 'asc',
        filter_model: JSON.stringify({
          status: statusOrFilter(['on_hand', 'deposited', 'presented']),
          cheque_date: dateLessThanFilter(chequesDueCutoff),
        }),
      }),
      inventoryItems: this.api.list<InventoryItemRow>('inventory-items', { page: 1, page_size: 200 }),
      buildings: this.api.list('buildings', { page: 1, page_size: 1 }),
      units: this.api.list('units', { page: 1, page_size: 1 }),
      warnings: this.warningsApi.getWarnings(),
    }).subscribe({
      next: (res) => {
        this.balanced = res.trialBalance.total_debit === res.trialBalance.total_credit;
        this.totalDebit = res.trialBalance.total_debit;
        this.totalCredit = res.trialBalance.total_credit;
        this.netIncome = res.balanceSheet.current_year_result;
        this.cashPosition = res.trialBalance.lines
          .filter((l) => CASH_ACCOUNT_CODES.has(l.account_code))
          .reduce((sum, l) => sum + l.balance, 0);
        this.activeContracts = res.activeContracts.meta.total;
        this.expiringContracts = res.expiringContracts.meta.total;
        this.chequesDueSoon = res.chequesDue.data;
        this.lowStockItems = res.inventoryItems.data.filter((i) => i.quantity_on_hand <= LOW_STOCK_THRESHOLD);
        this.buildingCount = res.buildings.meta.total;
        this.unitCount = res.units.meta.total;
        this.warningCount = res.warnings.total;
      },
    });
  }
}
