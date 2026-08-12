import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';

export interface WarningItem {
  category: string;
  severity: string; // info | warning | critical
  message: string;
  entity_type: string;
  entity_id: string | null;
}

export interface WarningsOut {
  items: WarningItem[];
  counts: Record<string, number>;
  total: number;
}

/**
 * Warnings page (backend/app/routers/warnings.py) -- a dedicated client, same
 * reasoning as ReportsApiService: a single aggregation result, not the paginated
 * {data, meta} list envelope every CRUD resource shares.
 */
@Injectable({ providedIn: 'root' })
export class WarningsApiService {
  constructor(private readonly http: HttpClient) {}

  getWarnings(): Observable<WarningsOut> {
    return this.http.get<WarningsOut>(`${API_BASE_URL}/warnings`);
  }
}
