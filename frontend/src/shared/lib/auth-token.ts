/**
 * Auth token management — stores JWT in memory + localStorage.
 *
 * In dev mode (AUTH_DISABLED=true on backend), no token is needed.
 * In local mode: token comes from POST /api/auth/login, stored in localStorage.
 * In production (Keycloak SSO): token set by Keycloak adapter after login.
 */

let _token: string | null = null;

const TOKEN_KEY = 'axisarch_token';

function loadToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function saveToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch { /* noop */ }
}

/** Store the access token (called by auth-context after login). */
export function setAuthToken(token: string | null): void {
  _token = token;
  saveToken(token);
}

/** Retrieve the current access token. */
export function getAuthToken(): string | null {
  if (_token) return _token;
  _token = loadToken();
  return _token;
}

/** Clear stored token (on logout). */
export function clearAuthToken(): void {
  _token = null;
  saveToken(null);
}

/**
 * Build the Authorization header object.
 * Returns empty object when no token is available.
 */
export function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
