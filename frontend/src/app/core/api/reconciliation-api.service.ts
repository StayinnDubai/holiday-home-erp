import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';

export interface MatchSuggestion {
  cheque_id: string;
  cheque_number: string;
  cheque_amount: number;
  cheque_date: string | null;
  bank_statement_entry_id: string;
  entry_amount: number;
  entry_date: string;
  day_difference: number;
}

export interface MatchSuggestionsResponse {
  bank_account_id: string;
  configured: boolean;
  suggestions: MatchSuggestion[];
}

/** Bank reconciliation matching (backend/app/routers/reconciliation.py) -- suggests
 * Cheque <-> Bank Statement - Original matches for a bank account. Confirming a
 * suggestion is a normal `CrudApiService.update('cheques', ...)` call, not
 * something this service does -- see bank-statement-original.component.ts. */
@Injectable({ providedIn: 'root' })
export class ReconciliationApiService {
  constructor(private readonly http: HttpClient) {}

  matchSuggestions(bankAccountId: string): Observable<MatchSuggestionsResponse> {
    return this.http.get<MatchSuggestionsResponse>(`${API_BASE_URL}/reconciliation/match-suggestions`, {
      params: new HttpParams().set('bank_account_id', bankAccountId),
    });
  }
}
