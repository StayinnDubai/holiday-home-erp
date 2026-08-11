import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/app-layout/app-layout.component';
import { PlaceholderComponent } from './shared/placeholder/placeholder.component';

import { UNITS_CONFIG } from './features/units/units.config';
import { BUILDINGS_CONFIG, BUILDING_CONTACTS_CONFIG, BUILDING_AMENITIES_CONFIG, BUILDING_DEPOSITS_CONFIG } from './features/buildings/buildings.config';
import { COUNTERPARTIES_CONFIG } from './features/counterparties/counterparties.config';
import { TENANCY_CONTRACTS_CONFIG, EJARI_REGISTRATIONS_CONFIG, RENTAL_AGREEMENTS_CONFIG } from './features/contracts/contracts.config';
import { DTCM_PERMITS_CONFIG, MOVE_IN_PERMITS_CONFIG } from './features/permits/permits.config';
import { CONVERSIONS_CONFIG } from './features/conversions/conversions.config';
import { RESERVATIONS_CONFIG, GUESTS_CONFIG } from './features/reservations/reservations.config';
import { TASKS_CONFIG } from './features/tasks/tasks.config';
import { BILLS_CONFIG, BILL_RECURRING_TEMPLATES_CONFIG } from './features/bills/bills.config';
import {
  CHART_OF_ACCOUNTS_CONFIG,
  JOURNAL_ENTRIES_CONFIG,
  CHEQUE_LEDGER_CONFIG,
  CASH_LEDGER_CONFIG,
  INVOICES_CONFIG,
  BANK_STATEMENT_CONFIG,
} from './features/accounting/accounting.config';
import {
  NUMBERING_CONFIG,
  TAX_CODES_CONFIG,
  SETUP_COST_TYPES_CONFIG,
  COST_TYPES_CONFIG,
  ASSET_CATEGORIES_CONFIG,
  REFERENCE_LISTS_CONFIG,
} from './features/settings/settings.config';

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
        loadComponent: () => PlaceholderComponent,
        data: { title: 'Dashboard', note: 'Role-aware landing page (doc §5.11) -- tiles defined once operational modules exist.' },
      },

      // ---- General ----
      { path: 'units', loadComponent: loadEntityPage, data: { title: 'Units', config: UNITS_CONFIG } },
      { path: 'buildings', loadComponent: loadEntityPage, data: { title: 'Buildings', config: BUILDINGS_CONFIG } },
      { path: 'buildings/contacts', loadComponent: loadEntityPage, data: { title: 'Building Contacts', config: BUILDING_CONTACTS_CONFIG } },
      { path: 'buildings/amenities', loadComponent: loadEntityPage, data: { title: 'Building Amenities', config: BUILDING_AMENITIES_CONFIG } },
      { path: 'buildings/deposits', loadComponent: loadEntityPage, data: { title: 'Building Deposits & Fees', config: BUILDING_DEPOSITS_CONFIG } },
      { path: 'counterparties', loadComponent: loadEntityPage, data: { title: 'Landlords & Counterparties', config: COUNTERPARTIES_CONFIG } },
      { path: 'contracts/tenancy', loadComponent: loadEntityPage, data: { title: 'Tenancy Contracts', config: TENANCY_CONTRACTS_CONFIG } },
      { path: 'contracts/tenancy/ejari', loadComponent: loadEntityPage, data: { title: 'Ejari Registrations', config: EJARI_REGISTRATIONS_CONFIG } },
      { path: 'contracts/rental', loadComponent: loadEntityPage, data: { title: 'Rental Agreements', config: RENTAL_AGREEMENTS_CONFIG } },
      { path: 'permits/dtcm', loadComponent: loadEntityPage, data: { title: 'DTCM Permits', config: DTCM_PERMITS_CONFIG } },
      { path: 'permits/move-in', loadComponent: loadEntityPage, data: { title: 'Move-in Permits', config: MOVE_IN_PERMITS_CONFIG } },
      { path: 'conversions', loadComponent: loadEntityPage, data: { title: 'Product-Line Conversions', config: CONVERSIONS_CONFIG } },

      // ---- Reservations ----
      { path: 'reservations', loadComponent: loadEntityPage, data: { title: 'Reservation List / Calendar', config: RESERVATIONS_CONFIG } },
      { path: 'reservations/guests', loadComponent: loadEntityPage, data: { title: 'Guests', config: GUESTS_CONFIG } },

      // ---- Tasks ----
      { path: 'tasks/board', loadComponent: loadEntityPage, data: { title: 'Task Board', config: TASKS_CONFIG } },
      { path: 'tasks/calendar', loadComponent: () => PlaceholderComponent, data: { title: 'Task Calendar', note: 'Calendar view of the same task data -- layered on once the Tasks milestone is built.' } },

      // ---- Bills ----
      { path: 'bills', loadComponent: loadEntityPage, data: { title: 'Bills', config: BILLS_CONFIG } },
      { path: 'bills/recurring', loadComponent: loadEntityPage, data: { title: 'Recurring Templates', config: BILL_RECURRING_TEMPLATES_CONFIG } },
      { path: 'bills/missing', loadComponent: () => PlaceholderComponent, data: { title: 'Missing Bill Report', note: 'Read-only report, not a CRUD entity -- built with Reporting (plan §9 milestone 6).' } },

      // ---- Accounting ----
      { path: 'accounting/chart-of-accounts', loadComponent: loadEntityPage, data: { title: 'Chart of Accounts', config: CHART_OF_ACCOUNTS_CONFIG } },
      { path: 'accounting/journal-entries', loadComponent: loadEntityPage, data: { title: 'Journal Entries', config: JOURNAL_ENTRIES_CONFIG } },
      { path: 'accounting/trial-balance', loadComponent: () => PlaceholderComponent, data: { title: 'Trial Balance', note: 'Read-only report, not a CRUD entity -- built with Reporting (plan §9 milestone 6).' } },
      { path: 'accounting/cheque-ledger', loadComponent: loadEntityPage, data: { title: 'Cheque Ledger', config: CHEQUE_LEDGER_CONFIG } },
      { path: 'accounting/cash-ledger', loadComponent: loadEntityPage, data: { title: 'Cash Ledger', config: CASH_LEDGER_CONFIG } },
      { path: 'accounting/invoices', loadComponent: loadEntityPage, data: { title: 'Invoices', config: INVOICES_CONFIG } },
      { path: 'accounting/bank-statement', loadComponent: loadEntityPage, data: { title: 'Bank Statement', config: BANK_STATEMENT_CONFIG } },

      // ---- Financial Reports (all read-only, not CRUD entities) ----
      { path: 'reports/pnl', loadComponent: () => PlaceholderComponent, data: { title: 'P&L' } },
      { path: 'reports/balance-sheet', loadComponent: () => PlaceholderComponent, data: { title: 'Balance Sheet' } },
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
      { path: 'settings/numbering', loadComponent: loadEntityPage, data: { title: 'Numbering', config: NUMBERING_CONFIG } },
      { path: 'settings/tax-codes', loadComponent: loadEntityPage, data: { title: 'Tax Codes', config: TAX_CODES_CONFIG } },
      { path: 'settings/setup-cost-types', loadComponent: loadEntityPage, data: { title: 'Setup Cost Types', config: SETUP_COST_TYPES_CONFIG } },
      { path: 'settings/cost-types', loadComponent: loadEntityPage, data: { title: 'Cost Types', config: COST_TYPES_CONFIG } },
      { path: 'settings/asset-categories', loadComponent: loadEntityPage, data: { title: 'Asset Categories', config: ASSET_CATEGORIES_CONFIG } },
      { path: 'settings/reference-lists', loadComponent: loadEntityPage, data: { title: 'Reference Lists', config: REFERENCE_LISTS_CONFIG } },

      { path: '**', loadComponent: () => PlaceholderComponent, data: { title: 'Not found' } },
    ],
  },
];
