/**
 * v1 has no Angular environment.*.ts build configurations yet (kept out of scope with
 * auth/tests, plan §7) -- a single constant is enough while there's only one target.
 * Move this to environment files the day staging/prod configs diverge from local dev.
 */
export const API_BASE_URL = 'http://localhost:8000/api/v1';
