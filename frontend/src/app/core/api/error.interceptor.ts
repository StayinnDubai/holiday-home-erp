import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MessageService } from 'primeng/api';
import { catchError, throwError } from 'rxjs';
import type { ApiErrorBody } from '../models/api.model';

/**
 * Normalizes every failed API call to the backend's {error:{code,message,details}} envelope
 * (plan §4/§6), logs it, and surfaces it as a toast -- forms still read `error.error.message`
 * / `.details` directly for inline field errors (details carries FastAPI's 422 field errors),
 * but background actions with no dedicated error UI of their own (inline grid edits, bulk
 * delete, ...) would otherwise fail silently without this.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const messageService = inject(MessageService);
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const body = err.error as ApiErrorBody | undefined;
      const message = body?.error?.message ?? err.message ?? 'Request failed.';
      console.error(`[API error] ${req.method} ${req.url} -> ${message}`, body?.error?.details ?? '');
      messageService.add({ severity: 'error', summary: 'Request failed', detail: message, life: 6000 });
      return throwError(() => err);
    })
  );
};
