import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';
import { PanelMenu } from 'primeng/panelmenu';
import type { MenuItem } from 'primeng/api';

/**
 * The one nav shell for v1 (plan §5): left sidebar, every parent group expandable
 * (PrimeNG PanelMenu, `multiple` so more than one group can stay open at once).
 * Everyone sees every module -- no role-based hiding yet, auth/roles are deferred
 * (plan §7). When roles land, this is the component that splits into an internal
 * vs. external layout.
 */
@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, PanelMenu],
  template: `
    <div class="shell">
      <aside class="sidebar">
        <div class="sidebar__brand">
          <span class="sidebar__brand-mark">HH</span>
          <span class="sidebar__brand-name">Holiday Home ERP</span>
        </div>
        <p-panelmenu [model]="menuItems" [multiple]="true" styleClass="sidebar__menu" />
      </aside>

      <div class="main">
        <header class="topbar">
          <h1 class="topbar__title">{{ currentTitle() }}</h1>
        </header>
        <main class="content">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        height: 100vh;
      }
      .shell {
        display: flex;
        height: 100%;
        background: #f1f5f9;
      }

      .sidebar {
        width: 280px;
        flex-shrink: 0;
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
      }
      .sidebar__brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 1.1rem 1.25rem;
        border-bottom: 1px solid #e2e8f0;
      }
      .sidebar__brand-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 8px;
        background: #0f766e;
        color: #fff;
        font-weight: 700;
        font-size: 0.8rem;
      }
      .sidebar__brand-name {
        font-weight: 700;
        font-size: 1rem;
        color: #0f172a;
      }
      .sidebar__menu {
        border: none;
        padding: 0.5rem;
      }

      .main {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
      }
      .topbar {
        height: 3.5rem;
        display: flex;
        align-items: center;
        padding: 0 1.5rem;
        background: #ffffff;
        border-bottom: 1px solid #e2e8f0;
      }
      .topbar__title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        color: #0f172a;
      }
      .content {
        flex: 1;
        overflow: auto;
        padding: 1.5rem;
      }
    `,
  ],
})
export class AppLayoutComponent implements OnInit {
  currentTitle = signal('Dashboard');

  /** IA mirrors plan §5's nav spec -- one module per top-level group, unchanged from the
   * mega menu version, just re-shaped for PanelMenu's flat MenuItem[] (children via `items`). */
  readonly menuItems: MenuItem[] = [
    { label: 'Dashboard', icon: 'pi pi-home', routerLink: '/dashboard' },
    {
      label: 'General',
      icon: 'pi pi-building',
      items: [
        { label: 'Units', routerLink: '/units' },
        { label: 'Buildings', routerLink: '/buildings' },
        { label: 'Landlords & Counterparties', routerLink: '/counterparties' },
        { label: 'Tenancy Contracts', routerLink: '/contracts/tenancy' },
        { label: 'Ejari Registrations', routerLink: '/contracts/tenancy/ejari' },
        { label: 'Rental Agreements', routerLink: '/contracts/rental' },
        { label: 'DTCM Permits', routerLink: '/permits/dtcm' },
        { label: 'Move-in Permits', routerLink: '/permits/move-in' },
        { label: 'Product-Line Conversions', routerLink: '/conversions' },
      ],
    },
    {
      label: 'Reservations',
      icon: 'pi pi-calendar',
      items: [
        { label: 'Reservation List / Calendar', routerLink: '/reservations' },
        { label: 'Guests', routerLink: '/reservations/guests' },
      ],
    },
    {
      label: 'Tasks',
      icon: 'pi pi-check-square',
      items: [
        { label: 'Task Board', routerLink: '/tasks/board' },
        { label: 'Task Calendar', routerLink: '/tasks/calendar' },
      ],
    },
    {
      label: 'Bills',
      icon: 'pi pi-file',
      items: [
        { label: 'Bills', routerLink: '/bills' },
        { label: 'Recurring Templates', routerLink: '/bills/recurring' },
        { label: 'Missing Bill Report', routerLink: '/bills/missing' },
      ],
    },
    {
      label: 'Accounting',
      icon: 'pi pi-book',
      items: [
        { label: 'Chart of Accounts', routerLink: '/accounting/chart-of-accounts' },
        { label: 'Journal Entries', routerLink: '/accounting/journal-entries' },
        { label: 'Trial Balance', routerLink: '/accounting/trial-balance' },
        { label: 'Cheque Ledger', routerLink: '/accounting/cheque-ledger' },
        { label: 'Cash Ledger', routerLink: '/accounting/cash-ledger' },
        { label: 'Invoices', routerLink: '/accounting/invoices' },
      ],
    },
    {
      label: 'Financial Reports',
      icon: 'pi pi-chart-bar',
      items: [
        { label: 'P&L', routerLink: '/reports/pnl' },
        { label: 'Balance Sheet', routerLink: '/reports/balance-sheet' },
        { label: 'Aged Receivables/Payables', routerLink: '/reports/aged-ar-ap' },
        { label: 'Compliance Dashboard', routerLink: '/reports/compliance-dashboard' },
        { label: 'Deposit Recovery', routerLink: '/reports/deposit-recovery' },
        { label: 'Cheque Position', routerLink: '/reports/cheque-position' },
      ],
    },
    {
      label: 'Settings',
      icon: 'pi pi-cog',
      items: [
        { label: 'Company', routerLink: '/settings/company' },
        { label: 'Numbering', routerLink: '/settings/numbering' },
        { label: 'Tax Codes', routerLink: '/settings/tax-codes' },
        { label: 'Setup Cost Types', routerLink: '/settings/setup-cost-types' },
        { label: 'Cost Types', routerLink: '/settings/cost-types' },
        { label: 'Asset Categories', routerLink: '/settings/asset-categories' },
        { label: 'Reference Lists', routerLink: '/settings/reference-lists' },
      ],
    },
  ];

  constructor(private readonly router: Router, private readonly route: ActivatedRoute) {}

  ngOnInit(): void {
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => this.deepestTitle())
      )
      .subscribe((title) => this.currentTitle.set(title));
    this.currentTitle.set(this.deepestTitle());
  }

  private deepestTitle(): string {
    let route = this.route.root;
    let title = 'Dashboard';
    while (route.firstChild) {
      route = route.firstChild;
      const data = route.snapshot.data;
      if (data && typeof data['title'] === 'string') {
        title = data['title'];
      }
    }
    return title;
  }
}
