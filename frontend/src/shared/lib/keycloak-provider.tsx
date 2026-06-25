'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { keycloakService } from './keycloak-service';

export interface KeycloakContextValue {
  /** Whether Keycloak has finished initialization. */
  initialized: boolean;
  /** Whether the current user is authenticated. */
  authenticated: boolean;
  /** Whether initialization is still loading. */
  loading: boolean;
  /** Current error message, if any. */
  error: string | null;
  /** Trigger Keycloak login. */
  login: () => Promise<void>;
  /** Trigger Keycloak logout. */
  logout: () => Promise<void>;
  /** Refresh the active token. */
  refreshToken: () => Promise<boolean>;
  /** Return the current user info from Keycloak. */  
  getUserInfo: () => {
    id?: string;
    name?: string;
    email?: string;
    preferred_username?: string;
    roles?: Record<string, unknown>;
  } | null;
}

const KeycloakContext = createContext<KeycloakContextValue | undefined>(undefined);

export interface KeycloakProviderProps {
  children: ReactNode;
}

export function KeycloakProvider({ children }: KeycloakProviderProps) {
  const [initialized, setInitialized] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initKeycloak = async () => {
      try {
        setLoading(true);
        setError(null);

        const isAuthenticated = await keycloakService.init();
        
        setInitialized(true);
        setAuthenticated(isAuthenticated);
        
        if (isAuthenticated) {
          console.log('Keycloak authentication succeeded. User info:', keycloakService.getUserInfo());
        }
      } catch (err) {
        console.error('Keycloak initialization failed:', err);
        setError(err instanceof Error ? err.message : 'Keycloak initialization failed');
        setInitialized(true);
        setAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    initKeycloak();
  }, []);

  const login = async () => {
    try {
      setError(null);
      await keycloakService.login();
    } catch (err) {
      console.error('Login failed:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const logout = async () => {
    try {
      setError(null);
      await keycloakService.logout();
      setAuthenticated(false);
    } catch (err) {
      console.error('Logout failed:', err);
      setError(err instanceof Error ? err.message : 'Logout failed');
    }
  };

  const refreshToken = async () => {
    try {
      setError(null);
      return await keycloakService.refreshToken();
    } catch (err) {
      console.error('Token refresh failed:', err);
      setError(err instanceof Error ? err.message : 'Token refresh failed');
      return false;
    }
  };

  const getUserInfo = () => {
    return keycloakService.getUserInfo();
  };

  const contextValue: KeycloakContextValue = {
    initialized,
    authenticated,
    loading,
    error,
    login,
    logout,
    refreshToken,
    getUserInfo,
  };

  return (
    <KeycloakContext.Provider value={contextValue}>
      {children}
    </KeycloakContext.Provider>
  );
}

export function useKeycloak(): KeycloakContextValue {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within a KeycloakProvider');
  }
  return context;
}