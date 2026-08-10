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
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
