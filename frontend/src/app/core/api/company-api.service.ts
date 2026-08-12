import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';
import { ItemResponse } from '../models/api.model';

/** Mirrors backend/app/schemas/foundation.py EntityOut. */
export interface CompanyRecord {
  id: string;
  legal_name: string;
  brand_name: string | null;
  trn: string | null;
  vat_number: string | null;
  license_number: string | null;
  website: string | null;
  phone_number: string | null;
  manager_name: string | null;
  date_of_registration: string | null;
  shareholders: string | null;
  address: string | null;
  financial_year_start_month: number;
  base_currency_id: string;
  base_currency_name: string | null;
  timezone: string;
}

export type CompanyUpdate = Partial<Omit<CompanyRecord, 'id'>>;

/**
 * Client for the singleton /company endpoint (doc §7 "Company") -- GET/PATCH only,
 * no list/create/delete, since D-1 fixes exactly one Entity row. Separate from
 * CrudApiService because there's no id in the URL and no list envelope to unwrap.
 */
@Injectable({ providedIn: 'root' })
export class CompanyApiService {
  constructor(private readonly http: HttpClient) {}

  get(): Observable<ItemResponse<CompanyRecord>> {
    return this.http.get<ItemResponse<CompanyRecord>>(`${API_BASE_URL}/company`);
  }

  update(payload: CompanyUpdate): Observable<ItemResponse<CompanyRecord>> {
    return this.http.patch<ItemResponse<CompanyRecord>>(`${API_BASE_URL}/company`, payload);
  }
}
