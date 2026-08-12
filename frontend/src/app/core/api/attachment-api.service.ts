import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-config';
import { ItemResponse, ListResponse } from '../models/api.model';

/** Mirrors backend/app/schemas/foundation.py AttachmentOut. */
export interface AttachmentRecord {
  id: string;
  entity_type: string;
  entity_id: string;
  file_path: string;
  original_filename: string;
  document_name: string | null;
  content_type: string | null;
  document_type: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  created_at: string;
}

export interface AttachmentUpdate {
  document_name?: string | null;
  document_type?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
}

/**
 * Client for the generic attachments endpoint (doc §5.3) -- any record can carry
 * files, keyed by (entity_type, entity_id) rather than a per-module table. Separate
 * from CrudApiService because uploads are multipart/form-data, not JSON, and the
 * backend route shape (query-string entity_type/entity_id on list, no /:id/file
 * download route wired into CrudApiService's generic shape) doesn't fit that
 * service's REST-resource assumptions.
 */
@Injectable({ providedIn: 'root' })
export class AttachmentApiService {
  constructor(private readonly http: HttpClient) {}

  list(entityType: string, entityId: string): Observable<ListResponse<AttachmentRecord>> {
    const params = new HttpParams().set('entity_type', entityType).set('entity_id', entityId);
    return this.http.get<ListResponse<AttachmentRecord>>(`${API_BASE_URL}/attachments`, { params });
  }

  /** No entity_type/entity_id filter -- every attachment across every module,
   * paginated. Backs the Documents register (features/documents). */
  listAll(page: number, pageSize: number, q?: string): Observable<ListResponse<AttachmentRecord>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize).set('sort_by', 'created_at').set('sort_dir', 'desc');
    if (q) params = params.set('q', q);
    return this.http.get<ListResponse<AttachmentRecord>>(`${API_BASE_URL}/attachments`, { params });
  }

  upload(entityType: string, entityId: string, file: File, documentName?: string): Observable<ItemResponse<AttachmentRecord>> {
    const form = new FormData();
    form.append('entity_type', entityType);
    form.append('entity_id', entityId);
    if (documentName) form.append('document_name', documentName);
    form.append('file', file);
    return this.http.post<ItemResponse<AttachmentRecord>>(`${API_BASE_URL}/attachments`, form);
  }

  update(attachmentId: string, payload: AttachmentUpdate): Observable<ItemResponse<AttachmentRecord>> {
    return this.http.patch<ItemResponse<AttachmentRecord>>(`${API_BASE_URL}/attachments/${attachmentId}`, payload);
  }

  remove(attachmentId: string): Observable<void> {
    return this.http.delete<void>(`${API_BASE_URL}/attachments/${attachmentId}`);
  }

  /** Direct, viewable/downloadable URL for an attachment's underlying file. */
  fileUrl(attachmentId: string): string {
    return `${API_BASE_URL}/attachments/${attachmentId}/file`;
  }
}
