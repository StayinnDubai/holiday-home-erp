import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';
import { ItemResponse, ListQuery, ListResponse } from '../models/api.model';

/**
 * One generic CRUD client for every REST resource (plan §4/§6), parametrized by
 * `resourcePath` instead of subclassed per module -- with ~25 modules needing the same
 * list/get/create/update/remove shape, a class per resource would just be repetition.
 * Feature pages pass their resourcePath from an EntityPageConfig (shared/crud/).
 */
@Injectable({ providedIn: 'root' })
export class CrudApiService {
  constructor(private readonly http: HttpClient) {}

  list<T>(resourcePath: string, query: ListQuery, extraParams: Record<string, string> = {}): Observable<ListResponse<T>> {
    let params = new HttpParams().set('page', query.page).set('page_size', query.page_size);
    if (query.sort_by) params = params.set('sort_by', query.sort_by);
    if (query.sort_dir) params = params.set('sort_dir', query.sort_dir);
    if (query.q) params = params.set('q', query.q);
    for (const [key, value] of Object.entries(extraParams)) {
      params = params.set(key, value);
    }
    return this.http.get<ListResponse<T>>(`${API_BASE_URL}/${resourcePath}`, { params });
  }

  create<T>(resourcePath: string, payload: unknown): Observable<ItemResponse<T>> {
    return this.http.post<ItemResponse<T>>(`${API_BASE_URL}/${resourcePath}`, payload);
  }

  update<T>(resourcePath: string, id: string, payload: unknown): Observable<ItemResponse<T>> {
    return this.http.patch<ItemResponse<T>>(`${API_BASE_URL}/${resourcePath}/${id}`, payload);
  }

  remove(resourcePath: string, id: string): Observable<void> {
    return this.http.delete<void>(`${API_BASE_URL}/${resourcePath}/${id}`);
  }
}
