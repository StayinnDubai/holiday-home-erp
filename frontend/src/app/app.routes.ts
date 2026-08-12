import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/app-layout/app-layout.component';
import { PlaceholderComponent } from './shared/placeholder/placeholder.component';

import { UNITS_CONFIG } from './features/units/units.config';
import { BUILDINGS_CONFIG, BUILDING_CONTACTS_CONFIG, BUILDING_AMENITIES_CONFIG, BUILDING_DEPOSITS_CONFIG } from './features/buildings/buildings.config';
import { COUNTERPARTIES_CONFIG } from './features/counterparties/counterparties.config';
import { COUNTERPARTY_GROUPS_CONFIG } from './features/counterparties/counterparty-groups.config';
import { LANDLORDS_CONFIG } from './features/counterparties/landlords.config';
import { INVENTORY_ITEMS_CONFIG, INVENTORY_MOVEMENTS_CONFIG } from './features/inventory/inventory.config';
import { TENANCY_CONTRACTS_CONFIG, EJARI_REGISTRATIONS_CONFIG } from './features/contracts/contracts.config';
import { CHART_OF_ACCOUNTS_CONFIG, CHEQUE_LEDGER_CONFIG, BANK_ACCOUNTS_CONFIG, JOURNAL_ENTRIES_CONFIG } from './features/accounting/accounting.config';
import { REFERENCE_LISTS_CONFIG, CURRENCIES_CONFIG, BANK_ACCOUNT_COLUMNS_CONFIG } from './features/settings/settings.config';
import { BILLS_CONFIG } from './features/bills/bills.config';

/**
 * Route tree mirrors the sidebar 1:1 (plan §5). Every CRUD-able module routes to the
 * generic EntityPageComponent bound to its EntityPageConfig via route `data.config`
 * (Angular's withComponentInputBinding, enabled in app.config.ts, binds it straight to
 * the component's `config` @Input -- no per-module wrapper component needed). Config
 * objects are plain data (no heavy imports), so importing them all here eagerly costs
 * nothing -- EntityPageComponent itself still lazy-loads via `loadComponent`.
 *
 * Left as PlaceholderComponent: Dashboard (needs real modules to build tiles from),
 * calendar/board views (different UI paradigm, layered on the same data later), and the
 * read-only report screens (not CRUD entities). Settings > Company is the one exception
 * to the generic-page rule that's actually built: a single record, not a list, so it
 * gets its own CompanySettingsComponent instead of EntityPageComponent.
 *
 * No auth/role guards in v1 (plan §7) -- every route is reachable by anyone.
 */
const loadEntityPage = () => import('./shared/crud/entity-page.component').then((m) => m.EntityPageComponent);

export const routes: Routes = [
  {
    path: '',
    component: AppLayoutComponent,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
        data: { title: 'Dashboard' },
      },

      // ---- General ----
      { path: 'units', loadComponent: loadEntityPage, data: { title: 'Units', config: UNITS_CONFIG } },
      { path: 'buildings', loadComponent: loadEntityPage, data: { title: 'Buildings', config: BUILDINGS_CONFIG } },
      { path: 'buildings/contacts', loadComponent: loadEntityPage, data: { title: 'Building Contacts', config: BUILDING_CONTACTS_CONFIG } },
      { path: 'buildings/amenities', loadComponent: loadEntityPage, data: { title: 'Building Amenities', config: BUILDING_AMENITIES_CONFIG } },
      { path: 'buildings/deposits', loadComponent: loadEntityPage, data: { title: 'Building Deposits & Fees', config: BUILDING_DEPOSITS_CONFIG } },
      { path: 'landlords', loadComponent: loadEntityPage, data: { title: 'Landlords', config: LANDLORDS_CONFIG } },
      { path: 'contracts/tenancy', loadComponent: loadEntityPage, data: { title: 'Tenancy Contracts', config: TENANCY_CONTRACTS_CONFIG } },
      { path: 'contracts/tenancy/ejari', loadComponent: loadEntityPage, data: { title: 'Ejari Registrations', config: EJARI_REGISTRATIONS_CONFIG } },
      { path: 'contracts/rental', loadComponent: () => PlaceholderComponent, data: { title: 'Rental Agreements', note: 'Not built yet -- the page is designed (see features/contracts/contracts.config.ts) but has no backend API yet.' } },
      { path: 'permits/dtcm', loadComponent: () => PlaceholderComponent, data: { title: 'DTCM Permits', note: 'Not built yet -- the page is designed (see features/permits/permits.config.ts) but has no backend API yet.' } },
      { path: 'permits/move-in', loadComponent: () => PlaceholderComponent, data: { title: 'Move-in Permits', note: 'Not built yet -- the page is designed (see features/permits/permits.config.ts) but has no backend API yet.' } },
      { path: 'conversions', loadComponent: () => PlaceholderComponent, data: { title: 'Product-Line Conversions', note: 'Not built yet -- the page is designed (see features/conversions/conversions.config.ts) but has no backend API yet.' } },

      // ---- Reservations ----
      { path: 'reservations', loadComponent: () => PlaceholderComponent, data: { title: 'Reservation List / Calendar', note: 'Not built yet -- the page is designed (see features/reservations/reservations.config.ts) but has no backend API yet.' } },
      { path: 'reservations/guests', loadComponent: () => PlaceholderComponent, data: { title: 'Guests', note: 'Not built yet -- the page is designed (see features/reservations/reservations.config.ts) but has no backend API yet.' } },

      // ---- Tasks ----
      { path: 'tasks/board', loadComponent: () => PlaceholderComponent, data: { title: 'Task Board', note: 'Not built yet -- the page is designed (see features/tasks/tasks.config.ts) but has no backend API yet.' } },
      { path: 'tasks/calendar', loadComponent: () => PlaceholderComponent, data: { title: 'Task Calendar', note: 'Calendar view of the same task data -- layered on once the Tasks milestone is built.' } },

      // ---- Bills ----
      { path: 'bills', loadComponent: loadEntityPage, data: { title: 'Bills', config: BILLS_CONFIG } },
      { path: 'bills/recurring', loadComponent: () => PlaceholderComponent, data: { title: 'Recurring Templates', note: 'Not built yet -- the page is designed (see features/bills/bills.config.ts) but has no backend API yet.' } },
      { path: 'bills/missing', loadComponent: () => PlaceholderComponent, data: { title: 'Missing Bill Report', note: 'Read-only report, not a CRUD entity -- built with Reporting (plan §9 milestone 6).' } },

      // ---- Accounting ----
      { path: 'accounting/chart-of-accounts', loadComponent: loadEntityPage, data: { title: 'Chart of Accounts', config: CHART_OF_ACCOUNTS_CONFIG } },
      { path: 'accounting/journal-entries', loadComponent: loadEntityPage, data: { title: 'Journal Entries', config: JOURNAL_ENTRIES_CONFIG } },
      {
        path: 'accounting/trial-balance',
        loadComponent: () => import('./features/reports/trial-balance.component').then((m) => m.TrialBalanceComponent),
        data: { title: 'Trial Balance' },
      },
      { path: 'accounting/cheque-ledger', loadComponent: loadEntityPage, data: { title: 'Cheque Ledger', config: CHEQUE_LEDGER_CONFIG } },
      { path: 'accounting/bank-accounts', loadComponent: loadEntityPage, data: { title: 'Bank Accounts', config: BANK_ACCOUNTS_CONFIG } },
      { path: 'accounting/cash-ledger', loadComponent: () => PlaceholderComponent, data: { title: 'Cash Ledger', note: 'Not built yet -- the page is designed (see features/accounting/accounting.config.ts) but has no backend API yet.' } },
      { path: 'accounting/invoices', loadComponent: () => PlaceholderComponent, data: { title: 'Invoices', note: 'Not built yet -- the page is designed (see features/accounting/accounting.config.ts) but has no backend API yet.' } },
      {
        path: 'accounting/bank-statement',
        loadComponent: () =>
          import('./features/accounting/bank-statement-original.component').then((m) => m.BankStatementOriginalComponent),
        data: { title: 'Bank Statement - Original' },
      },
      {
        path: 'accounting/bank-statement-reconciliation',
        loadComponent: () =>
          import('./features/accounting/bank-statement-reconciliation.component').then((m) => m.BankStatementReconciliationComponent),
        data: { title: 'Bank Statement - Reconciliation' },
      },
      { path: 'accounting/counterparties', loadComponent: loadEntityPage, data: { title: 'Counterparties', config: COUNTERPARTIES_CONFIG } },
      { path: 'accounting/counterparty-groups', loadComponent: loadEntityPage, data: { title: 'Counterparty Group', config: COUNTERPARTY_GROUPS_CONFIG } },
      { path: 'accounting/inventory-items', loadComponent: loadEntityPage, data: { title: 'Inventory Items', config: INVENTORY_ITEMS_CONFIG } },
      { path: 'accounting/inventory-movements', loadComponent: loadEntityPage, data: { title: 'Inventory Movements', config: INVENTORY_MOVEMENTS_CONFIG } },

      // ---- Financial Reports (all read-only, not CRUD entities) ----
      {
        path: 'reports/pnl',
        loadComponent: () => import('./features/reports/pnl.component').then((m) => m.PnlComponent),
        data: { title: 'P&L' },
      },
      {
        path: 'reports/balance-sheet',
        loadComponent: () => import('./features/reports/balance-sheet.component').then((m) => m.BalanceSheetComponent),
        data: { title: 'Balance Sheet' },
      },
      { path: 'reports/aged-ar-ap', loadComponent: () => PlaceholderComponent, data: { title: 'Aged Receivables/Payables' } },
      { path: 'reports/compliance-dashboard', loadComponent: () => PlaceholderComponent, data: { title: 'Compliance Dashboard' } },
      { path: 'reports/deposit-recovery', loadComponent: () => PlaceholderComponent, data: { title: 'Deposit Recovery' } },
      { path: 'reports/cheque-position', loadComponent: () => PlaceholderComponent, data: { title: 'Cheque Position' } },

      // ---- Settings ----
      {
        path: 'settings/company',
        loadComponent: () => import('./features/settings/company-settings.component').then((m) => m.CompanySettingsComponent),
        data: { title: 'Company' },
      },
      { path: 'settings/currencies', loadComponent: loadEntityPage, data: { title: 'Currencies', config: CURRENCIES_CONFIG } },
      { path: 'settings/bank-account-columns', loadComponent: loadEntityPage, data: { title: 'Bank Account Columns', config: BANK_ACCOUNT_COLUMNS_CONFIG } },
      { path: 'settings/numbering', loadComponent: () => PlaceholderComponent, data: { title: 'Numbering', note: 'Not built yet -- the page is designed (see features/settings/settings.config.ts) but has no backend API yet. Document numbering itself already works internally via backend/app/services/numbering.py; this page is for configuring its rules.' } },
      { path: 'settings/tax-codes', loadComponent: () => PlaceholderComponent, data: { title: 'Tax Codes', note: 'Not built yet -- the page is designed (see features/settings/settings.config.ts) but has no backend API yet.' } },
      { path: 'settings/setup-cost-types', loadComponent: () => PlaceholderComponent, data: { title: 'Setup Cost Types', note: 'Not built yet -- the page is designed (see features/settings/settings.config.ts) but has no backend API yet.' } },
      { path: 'settings/cost-types', loadComponent: () => PlaceholderComponent, data: { title: 'Cost Types', note: 'Not built yet -- the page is designed (see features/settings/settings.config.ts) but has no backend API yet.' } },
      { path: 'settings/asset-categories', loadComponent: () => PlaceholderComponent, data: { title: 'Asset Categories', note: 'Not built yet -- the page is designed (see features/settings/settings.config.ts) but has no backend API yet.' } },
      { path: 'settings/reference-lists', loadComponent: loadEntityPage, data: { title: 'Reference Lists', config: REFERENCE_LISTS_CONFIG } },

      { path: '**', loadComponent: () => PlaceholderComponent, data: { title: 'Not found' } },
    ],
  },
];
