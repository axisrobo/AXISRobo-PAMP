import { authHeaders, clearAuthToken } from '@/shared/lib/auth-token';
import { keycloakService } from '@/shared/lib/keycloak-service';

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, '');
  }

  // In local browser dev, call backend directly to avoid Next rewrite proxy
  // reset/hangup on long-running endpoints (e.g. AI checks).
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `${protocol}//${hostname}:4000/api`;
    }
  }

  return '/api';
}

export const API_BASE = resolveApiBase();
const AUTH_DISABLED = process.env.NEXT_PUBLIC_AUTH_DISABLED === 'true';
const AUTH_MODE = (process.env.NEXT_PUBLIC_AUTH_MODE as string) || 'dev';

/* ── 401/403 handling ── */

/** Shared refresh promise to deduplicate concurrent 401 refreshes */
let _refreshPromise: Promise<boolean> | null = null;
/** Prevent redirect loops — survives page reloads via sessionStorage */
let _redirecting = false;
const REDIRECT_COOLDOWN_MS = 15_000; // 15-second cooldown between redirects
const REDIRECT_TS_KEY = '__eam_redirect_ts';

function isInRedirectCooldown(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const ts = sessionStorage.getItem(REDIRECT_TS_KEY);
    if (!ts) return false;
    return Date.now() - Number(ts) < REDIRECT_COOLDOWN_MS;
  } catch { return false; }
}

function markRedirect(): void {
  try { sessionStorage.setItem(REDIRECT_TS_KEY, String(Date.now())); } catch {}
}

async function tryRefreshToken(): Promise<boolean> {
  // Local JWT auth has no silent refresh (no Keycloak). Skip the dead path.
  if (AUTH_DISABLED || AUTH_MODE === 'local' || _redirecting) return false;
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = keycloakService.refreshToken().finally(() => { _refreshPromise = null; });
  return _refreshPromise;
}

function redirectToLogin(): void {
  if (AUTH_DISABLED || _redirecting || isInRedirectCooldown()) return;
  _redirecting = true;
  markRedirect();
  // Local mode: clear the stale token and go to the local login page,
  // never through the (uninitialized) Keycloak login flow.
  if (AUTH_MODE === 'local') {
    clearAuthToken();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
    return;
  }
  keycloakService.login();
}

function redirectToForbidden(): void {
  if (_redirecting || isInRedirectCooldown()) return;
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/forbidden')) {
    _redirecting = true;
    markRedirect();
    window.location.href = '/forbidden';
  }
}

export interface ApiEnvelope<T = unknown> {
  code: number;
  message: string;
  data: T;
  timestamp: number;
}

function isEnvelope(value: any): value is ApiEnvelope {
  return (
    value &&
    typeof value === 'object' &&
    typeof value.code === 'number' &&
    typeof value.message === 'string' &&
    typeof value.timestamp === 'number' &&
    'data' in value
  );
}

async function readJsonSafe(res: Response): Promise<any | null> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const doFetch = () =>
    fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
        ...options?.headers,
      },
    });

  let res = await doFetch();

  // 401: try one silent token refresh, then retry
  if (res.status === 401 && !AUTH_DISABLED) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      res = await doFetch();
    }
    if (res.status === 401) {
      redirectToLogin();
      throw new Error('Session expired');
    }
  }

  // 403: redirect to forbidden page
  if (res.status === 403) {
    redirectToForbidden();
    throw new Error('Access denied');
  }

  const contentType = res.headers.get('content-type') || '';
  const maybeJson = contentType.includes('application/json') || contentType.includes('+json');
  const body = maybeJson ? await readJsonSafe(res) : null;

  if (isEnvelope(body)) {
    // Transport-level error
    if (!res.ok) throw new Error(body.message || `API error: ${res.status}`);
    // Business-level error
    if (body.code !== 200) throw new Error(body.message || 'Business processing failed');
    return body.data as T;
  }

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return (body ?? (await readJsonSafe(res))) as T;
}

export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

export const api = {
  get: <T>(endpoint: string, params?: Record<string, any>) =>
    fetchApi<T>(`${endpoint}${params ? buildQueryString(params) : ''}`),
  post: <T>(endpoint: string, data: any) =>
    fetchApi<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: any) =>
    fetchApi<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: any) =>
    fetchApi<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) =>
    fetchApi<T>(endpoint, { method: 'DELETE' }),
  /** Upload multipart/form-data and unwrap the response envelope. */
  postForm: async <T>(endpoint: string, formData: FormData): Promise<T> => {
    const doFetch = () =>
      fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        body: formData,
        headers: {
          // Do NOT set Content-Type — browser sets multipart boundary automatically
          ...authHeaders(),
        },
      });

    let res = await doFetch();

    if (res.status === 401 && !AUTH_DISABLED) {
      const refreshed = await tryRefreshToken();
      if (refreshed) res = await doFetch();
      if (res.status === 401) {
        redirectToLogin();
        throw new Error('Session expired');
      }
    }

    if (res.status === 403) {
      redirectToForbidden();
      throw new Error('Access denied');
    }

    const body = await readJsonSafe(res);
    if (isEnvelope(body)) {
      if (!res.ok) throw new Error(body.message || `API error: ${res.status}`);
      if (body.code !== 200) throw new Error(body.message || 'Business processing failed');
      return body.data as T;
    }
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return body as T;
  },
};

/**
 * Fetch a blob (e.g. CSV export) with auth headers included.
 * Use this instead of raw fetch() for authenticated file downloads.
 */
export async function fetchBlob(url: string): Promise<Blob> {
  const res = await authFetch(url);
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  return res.blob();
}

/**
 * Auth-aware fetch wrapper. Adds Bearer token and handles 401/403 globally.
 * Use this for any raw fetch() call that needs auth (e.g. file uploads).
 */
export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const doFetch = () =>
    fetch(input, {
      ...init,
      headers: {
        ...authHeaders(),
        ...init?.headers,
      },
    });

  let res = await doFetch();

  if (res.status === 401 && !AUTH_DISABLED) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      res = await doFetch();
    }
    if (res.status === 401) {
      redirectToLogin();
      throw new Error('Session expired');
    }
  }

  if (res.status === 403) {
    redirectToForbidden();
    throw new Error('Access denied');
  }

  return res;
}
