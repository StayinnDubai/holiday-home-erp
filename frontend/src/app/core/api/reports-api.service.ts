import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';

export interface AccountBalanceLine {
  account_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  normal_balance: string;
  debit: number;
  credit: number;
  balance: number;
}

export interface TrialBalance {
  as_of: string;
  lines: AccountBalanceLine[];
  total_debit: number;
  total_credit: number;
}

export interface Pnl {
  date_from: string;
  date_to: string;
  revenue_lines: AccountBalanceLine[];
  cost_lines: AccountBalanceLine[];
  total_revenue: number;
  total_cost: number;
  net_income: number;
}

export interface BalanceSheet {
  as_of: string;
  asset_lines: AccountBalanceLine[];
  liability_lines: AccountBalanceLine[];
  equity_lines: AccountBalanceLine[];
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  current_year_result: number;
}

export interface AgedPayableLine {
  bill_id: string;
  bill_number: string;
  supplier_name: string;
  due_date: string | null;
  amount: number;
  bucket: string;
}

export interface AgedPayables {
  as_of: string;
  lines: AgedPayableLine[];
  bucket_totals: Record<string, number>;
  grand_total: number;
}

export interface ChequePositionGroup {
  direction: string;
  status: string;
  count: number;
  total_amount: number;
}

export interface ChequePosition {
  as_of: string;
  groups: ChequePositionGroup[];
}

/**
 * Financial Reports (backend/app/routers/reports.py) -- a dedicated client rather than
 * CrudApiService, since these are single-object aggregation results (not the
 * paginated {data, meta} list envelope every CRUD resource shares).
 */
@Injectable({ providedIn: 'root' })
export class ReportsApiService {
  constructor(private readonly http: HttpClient) {}

  trialBalance(asOf: string): Observable<TrialBalance> {
    return this.http.get<TrialBalance>(`${API_BASE_URL}/reports/trial-balance`, { params: new HttpParams().set('as_of', asOf) });
  }

  pnl(dateFrom: string, dateTo: string): Observable<Pnl> {
    return this.http.get<Pnl>(`${API_BASE_URL}/reports/pnl`, {
      params: new HttpParams().set('date_from', dateFrom).set('date_to', dateTo),
    });
  }

  balanceSheet(asOf: string): Observable<BalanceSheet> {
    return this.http.get<BalanceSheet>(`${API_BASE_URL}/reports/balance-sheet`, { params: new HttpParams().set('as_of', asOf) });
  }

  agedPayables(asOf: string): Observable<AgedPayables> {
    return this.http.get<AgedPayables>(`${API_BASE_URL}/reports/aged-payables`, { params: new HttpParams().set('as_of', asOf) });
  }

  chequePosition(asOf: string): Observable<ChequePosition> {
    return this.http.get<ChequePosition>(`${API_BASE_URL}/reports/cheque-position`, { params: new HttpParams().set('as_of', asOf) });
  }
}
