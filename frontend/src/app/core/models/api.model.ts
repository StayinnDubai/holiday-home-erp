/** Mirrors the backend envelope in backend/app/schemas/common.py (plan §4/§6). */
export interface ListMeta {
  page: number;
  page_size: number;
  total: number;
}

export interface ListResponse<T> {
  data: T[];
  meta: ListMeta;
}

export interface ItemResponse<T> {
  data: T;
}

/** Shared list-query shape, identical to backend/app/core/pagination.py's PaginationParams. */
export interface ListQuery {
  page: number;
  page_size: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  q?: string;
  /** JSON-serialized ag-Grid filterModel, one entry per filtered column -- see
   * backend/app/core/pagination.py's `apply_filters` for the shape it expects. */
  filter_model?: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
