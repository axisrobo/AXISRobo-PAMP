'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { authHeaders, setAuthToken, clearAuthToken, getAuthToken } from '@/shared/lib/auth-token';
import { keycloakService } from '@/shared/lib/keycloak-service';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  /** @deprecated Use `roles` instead. Kept for backward compat (highest-precedence role). */
  role: string;
  /** All resolved roles for the current user (e.g. ["normal_user", "ea_reviewer"]). */
  roles: string[];
  permissions: string[];
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  /** Prevent LoginGate from auto-triggering login after fatal fetch failures */
  suppressAutoLogin: boolean;
  /** Check if the current user has a specific permission */
  hasPermission: (resource: string, scope?: string) => boolean;
  /** Check if the current user has one of the given roles */
  hasRole: (...roles: string[]) => boolean;
  /** Refresh user info from the server */
  refresh: () => Promise<void>;
  /** Log in via Keycloak */
  login: (username?: string, password?: string) => Promise<void>;
  /** Log out via Keycloak */ 
  logout: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
const AUTH_DISABLED = process.env.NEXT_PUBLIC_AUTH_DISABLED === 'true';
const AUTH_MODE = (process.env.NEXT_PUBLIC_AUTH_MODE as string) || 'dev';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [suppressAutoLogin, setSuppressAutoLogin] = useState(false);

  const decodeUser = (body: any): AuthUser => {
    let raw: any;
    if (body && typeof body === 'object' && 'data' in body && 'code' in body && 'message' in body) {
      raw = body.data;
    } else {
      raw = body;
    }
    // Ensure `roles` is always populated even if the backend only returns `role`
    if (raw && !Array.isArray(raw.roles)) {
      raw.roles = raw.role ? [raw.role] : ['normal_user'];
    }
    return raw as AuthUser;
  };

  const fetchUser = useCallback(async () => {
    const hasToken = !!getAuthToken();
    if (AUTH_MODE === 'oidc' && !keycloakService.isAuthenticated()) {
      setUser(null);
      setLoading(false);
      setSuppressAutoLogin(false);
      return;
    }
    if (AUTH_MODE === 'local' && !hasToken) {
      setUser(null);
      setLoading(false);
      setSuppressAutoLogin(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuppressAutoLogin(false);
      
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
      });

      if (!res.ok) {
        if (res.status === 401) {
          // The token may have expired, so try refreshing it.
          const refreshed = await keycloakService.refreshToken();
          if (refreshed) {
            // Retry the request after a successful refresh.
            const retryRes = await fetch(`${API_BASE}/auth/me`, {
              headers: { 'Content-Type': 'application/json', ...authHeaders() },
            });
            if (retryRes.ok) {
              const body = await retryRes.json();
              setUser(decodeUser(body));
              setLoading(false);
              return;
            }
          }
          // If the refresh fails, the user must log in again.
          throw new Error('Your session has expired. Please sign in again.');
        }
        throw new Error(`Failed to load user information: ${res.status} ${res.statusText}`);
      }

      const body = await res.json();
      setUser(decodeUser(body));
      
    } catch (err) {
      console.error('Failed to load user information:', err);
      setError(err instanceof Error ? err.message : 'Failed to load user information');
      setUser(null);
      // Always suppress auto-login on failure to prevent redirect loops.
      // The user can manually click the retry button shown by LoginGate.
      setSuppressAutoLogin(true);
      if (err instanceof TypeError && err.message.includes('fetch')) {
        console.warn('The network request failed. The server may be unreachable or there may be a certificate issue.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      try {
        setLoading(true);

        if (AUTH_MODE === 'dev' || AUTH_DISABLED) {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Content-Type': 'application/json' },
          });
          if (res.ok) {
            const body = await res.json();
            setUser(decodeUser(body));
          } else {
            setError('Failed to load the development user');
            setSuppressAutoLogin(true);
          }
          setLoading(false);
          return;
        }

        if (AUTH_MODE === 'local') {
          const token = getAuthToken();
          if (!token) {
            setLoading(false);
            return;
          }
          await fetchUser();
          return;
        }

        if (AUTH_MODE === 'oidc') {
          const authenticated = await keycloakService.init();
          if (authenticated) {
            await fetchUser();
          } else {
            setLoading(false);
          }
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        setError('Failed to initialize the authentication system');
        setSuppressAutoLogin(true);
        setLoading(false);
      }
    };

    initAuth();
  }, [fetchUser]);

  const login = useCallback(async (username?: string, password?: string) => {
    try {
      if (AUTH_MODE === 'local' && username && password) {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.message || body.detail || 'Login failed');
        }
        const body = await res.json();
        const data = body.data || body;
        if (data.access_token) {
          setAuthToken(data.access_token);
        }
        if (data.user) {
          setUser(decodeUser(data.user));
        }
        setLoading(false);
        setError(null);
        return;
      }
      if (AUTH_MODE === 'oidc') {
        await keycloakService.login();
      }
    } catch (error) {
      console.error('Login failed:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      if (AUTH_MODE === 'local') {
        clearAuthToken();
        setUser(null);
        return;
      }
      if (AUTH_MODE === 'oidc') {
        await keycloakService.logout();
      }
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, []);

  const hasPermission = useCallback(
    (resource: string, scope: string = 'read'): boolean => {
      if (!user) return false;
      const perms = user.permissions;
      // Wildcard admin
      if (perms.includes('*:*')) return true;
      // Exact match
      if (perms.includes(`${resource}:${scope}`)) return true;
      // Resource wildcard
      if (perms.includes(`${resource}:*`)) return true;
      return false;
    },
    [user]
  );

  const hasRole = useCallback(
    (...roles: string[]): boolean => {
      if (!user) return false;
      // Check if any of the user's roles match any of the requested roles
      return user.roles.some((r) => roles.includes(r));
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        suppressAutoLogin,
        hasPermission,
        hasRole,
        refresh: fetchUser,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

/**
 * Convenience hook — check a single permission.
 *
 * Usage:
 *   const canEdit = usePermission('ea_request', 'write');
 */
export function usePermission(resource: string, scope: string = 'read'): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(resource, scope);
}
