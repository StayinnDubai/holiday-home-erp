import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import type { ApiErrorBody } from '../models/api.model';

/**
 * Normalizes every failed API call to the backend's {error:{code,message,details}} envelope
 * (plan §4/§6) and logs it. No toast/notification service in v1 yet -- forms read
 * `error.error.message` / `.details` directly (details carries FastAPI's 422 field errors).
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const body = err.error as ApiErrorBody | undefined;
      const message = body?.error?.message ?? err.message ?? 'Request failed.';
      console.error(`[API error] ${req.method} ${req.url} -> ${message}`, body?.error?.details ?? '');
      return throwError(() => err);
    })
  );
