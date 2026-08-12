import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { WarningItem, WarningsApiService, WarningsOut } from '../../core/api/warnings-api.service';

const CATEGORY_LABELS: Record<string, string> = {
  overdue_bill: 'Overdue bills',
  overdue_invoice: 'Overdue invoices',
  bounced_cheque: 'Bounced cheques',
  expiring_contract: 'Contracts expiring soon',
  low_stock: 'Low stock inventory',
  ejari_variance: 'Ejari variances',
  dtcm_permit_expiring: 'DTCM permits expiring soon',
  dtcm_operator_license_expiring: 'DTCM operator licences expiring soon',
  trial_balance_out_of_balance: 'Trial balance out of balance',
};

const CATEGORY_LINKS: Record<string, string> = {
  overdue_bill: '/bills',
  overdue_invoice: '/accounting/invoices',
  bounced_cheque: '/accounting/cheque-ledger',
  expiring_contract: '/contracts/tenancy',
  low_stock: '/accounting/inventory-items',
  ejari_variance: '/contracts/tenancy/ejari',
  dtcm_permit_expiring: '/permits/dtcm',
  dtcm_operator_license_expiring: '/permits/dtcm',
  trial_balance_out_of_balance: '/accounting/trial-balance',
};

interface CategoryGroup {
  category: string;
  label: string;
  link: string | null;
  items: WarningItem[];
}

/**
 * Dedicated read-only Warnings page (repurposes the reports/compliance-dashboard
 * nav slot) -- aggregates existing, already-computable concerns into one place. No
 * header bell/dropdown: there's no auth/user system yet, so there's no per-user
 * read/unread state to track (resolved with the user directly during planning).
 */
@Component({
  selector: 'app-warnings',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="panel">
      <div class="panel__header">
        <div>
          <h2 class="panel__title">Warnings</h2>
          <p class="panel__subtitle">Everything that needs attention, in one place -- overdue bills/invoices, bounced cheques, expiring contracts, low stock, Ejari variances.</p>
        </div>
        <div class="panel__total" *ngIf="warnings">{{ warnings.total }} total</div>
      </div>

      <div class="panel__body">
        <p class="panel__hint" *ngIf="loading">Loading...</p>
        <p class="panel__hint panel__hint--good" *ngIf="!loading && warnings && warnings.total === 0">
          Nothing needs attention right now.
        </p>

        <div class="group" *ngFor="let g of groups">
          <div class="group__header">
            <h3 class="group__title">{{ g.label }}</h3>
            <span class="group__count">{{ g.items.length }}</span>
            <a class="group__link" *ngIf="g.link" [routerLink]="g.link">View</a>
          </div>
          <ul class="group__list">
            <li *ngFor="let item of g.items" [class]="'item item--' + item.severity">
              {{ item.message }}
            </li>
          </ul>
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
        max-width: 46rem;
      }
      .panel__total {
        font-size: 0.85rem;
        font-weight: 700;
        color: #334155;
        background: #f1f5f9;
        border-radius: 999px;
        padding: 0.3rem 0.8rem;
        white-space: nowrap;
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
      .panel__hint--good {
        color: #166534;
      }
      .group {
        margin-bottom: 1.25rem;
      }
      .group__header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.5rem;
      }
      .group__title {
        margin: 0;
        font-size: 0.92rem;
        font-weight: 700;
        color: #0f172a;
      }
      .group__count {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748b;
        background: #f1f5f9;
        border-radius: 999px;
        padding: 0.1rem 0.55rem;
      }
      .group__link {
        margin-left: auto;
        font-size: 0.82rem;
        color: #0f766e;
        font-weight: 600;
        text-decoration: none;
      }
      .group__link:hover {
        text-decoration: underline;
      }
      .group__list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
      }
      .item {
        font-size: 0.88rem;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        border-left: 3px solid #cbd5e1;
        background: #f8fafc;
        color: #0f172a;
      }
      .item--info {
        border-left-color: #38bdf8;
      }
      .item--warning {
        border-left-color: #f59e0b;
        background: #fffbeb;
      }
      .item--critical {
        border-left-color: #dc2626;
        background: #fef2f2;
      }
    `,
  ],
})
export class WarningsComponent implements OnInit {
  warnings: WarningsOut | null = null;
  groups: CategoryGroup[] = [];
  loading = false;

  constructor(private readonly api: WarningsApiService) {}

  ngOnInit(): void {
    this.loading = true;
    this.api.getWarnings().subscribe({
      next: (res) => {
        this.warnings = res;
        this.groups = this.buildGroups(res.items);
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  private buildGroups(items: WarningItem[]): CategoryGroup[] {
    const byCategory = new Map<string, WarningItem[]>();
    for (const item of items) {
      const list = byCategory.get(item.category) ?? [];
      list.push(item);
      byCategory.set(item.category, list);
    }
    return Array.from(byCategory.entries()).map(([category, categoryItems]) => ({
      category,
      label: CATEGORY_LABELS[category] ?? category,
      link: CATEGORY_LINKS[category] ?? null,
      items: categoryItems,
    }));
  }
}
