/**
 * Keycloak authentication service.
 *
 * Handles Keycloak initialization, login, logout, and token management.
 */
import Keycloak from 'keycloak-js';
import { keycloakConfig, keycloakInitOptions } from './keycloak-config';
import { setAuthToken } from './auth-token';

class KeycloakService {
  private keycloak: Keycloak | null = null;
  private initPromise: Promise<boolean> | null = null;

  /**
   * Return the Keycloak instance.
   */
  getInstance(): Keycloak | null {
    return this.keycloak;
  }

  /**
   * Initialize Keycloak.
   */
  async init(): Promise<boolean> {
    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = this._doInit();
    return this.initPromise;
  }

  private async _doInit(): Promise<boolean> {
    try {
      // Initialize Keycloak only in the browser.
      if (typeof window === 'undefined') {
        return false;
      }

      console.log('[Keycloak] Starting initialization with config:', JSON.stringify(keycloakConfig));
      console.log('[Keycloak] Initialization options:', JSON.stringify({...keycloakInitOptions, silentCheckSsoRedirectUri: keycloakInitOptions.silentCheckSsoRedirectUri}));
      
      this.keycloak = new Keycloak(keycloakConfig);

      // Add a timeout guard so init cannot hang forever.
      const timeoutMs = 10000;
      const initPromise = this.keycloak.init(keycloakInitOptions);
      const timeoutPromise = new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error(`Keycloak init timed out (${timeoutMs}ms)`)), timeoutMs)
      );
      
      const authenticated = await Promise.race([initPromise, timeoutPromise]);
      console.log('[Keycloak] Initialization finished. Authenticated:', authenticated);

      if (authenticated && this.keycloak.token) {
        // Store the token in the global auth token manager.
        setAuthToken(this.keycloak.token);
        
        // Start the token refresh timer.
        this.setupTokenRefresh();
        
        console.log('Keycloak authentication succeeded');
      } else {
        console.log('User is not authenticated');
      }

      return authenticated;
    } catch (error) {
      console.error('[Keycloak] Initialization failed:', error);
      console.error('[Keycloak] Error details:', error instanceof Error ? error.message : String(error));
      // Do not keep the app in a loading state if init fails; allow the page to continue.
      this.initPromise = null; // Allow retries.
      return false;
    }
  }

  /**
   * Log in.
   */
  async login(): Promise<void> {
    if (!this.keycloak) {
      await this.init();
    }
    
    if (this.keycloak) {
      await this.keycloak.login({
        redirectUri: window.location.origin + window.location.pathname
      });
    }
  }

  /**
   * Log out.
   */
  async logout(): Promise<void> {
    if (this.keycloak) {
      setAuthToken(null); // Clear the token.
      await this.keycloak.logout({
        redirectUri: window.location.origin
      });
    }
  }

  /**
   * Check whether the user is authenticated.
   */
  isAuthenticated(): boolean {
    return this.keycloak?.authenticated || false;
  }

  /**
   * Get the current token.
   */
  getToken(): string | undefined {
    return this.keycloak?.token;
  }

  /**
   * Refresh the token.
   */
  async refreshToken(): Promise<boolean> {
    if (!this.keycloak) {
      return false;
    }

    try {
      const refreshed = await this.keycloak.updateToken(30); // Refresh if the token expires within 30 seconds.
      if (refreshed && this.keycloak.token) {
        setAuthToken(this.keycloak.token);
        console.log('Token refreshed');
      }
      return refreshed;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  /**
   * Set up automatic token refresh.
   */
  private setupTokenRefresh(): void {
    if (!this.keycloak) return;

    // Check every 30 seconds whether the token needs to be refreshed.
    setInterval(async () => {
      try {
        await this.refreshToken();
      } catch (error) {
        console.error('Automatic token refresh failed:', error);
      }
    }, 30000);
  }

  /**
   * Get the current user information.
   */
  getUserInfo(): {
    id: string;
    name?: string;
    email?: string;
    preferred_username?: string;
    roles?: Record<string, unknown>;
  } | null {
    if (!this.keycloak || !this.keycloak.tokenParsed) {
      return null;
    }

    return {
      id: this.keycloak.tokenParsed.preferred_username || this.keycloak.tokenParsed.sub,
      name: this.keycloak.tokenParsed.name || this.keycloak.tokenParsed.preferred_username,
      email: this.keycloak.tokenParsed.email,
      roles: this.keycloak.tokenParsed.resource_access || {}
    };
  }
}

// Singleton instance.
export const keycloakService = new KeycloakService();