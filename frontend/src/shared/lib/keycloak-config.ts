/**
 * Keycloak configuration.
 *
 * Builds the Keycloak client config from environment variables.
 */

import { appConfig } from '@/shared/lib/app-config';

export interface KeycloakConfig {
  url: string;
  realm: string;
  clientId: string;
}

export const keycloakConfig: KeycloakConfig = {
  url: process.env.NEXT_PUBLIC_KEYCLOAK_SERVER_URL || process.env.KEYCLOAK_SERVER_URL || appConfig.keycloakDefaultUrl,
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || process.env.KEYCLOAK_REALM || 'myapp',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || process.env.KEYCLOAK_CLIENT_ID || 'tap-eam-8a473212f5e306df-f'
};

export const keycloakInitOptions = {
  onLoad: 'check-sso' as const,
  silentCheckSsoRedirectUri: 
    typeof window !== 'undefined' 
      ? window.location.origin + '/silent-check-sso.html' 
      : undefined,
  checkLoginIframe: false, // Avoid cross-origin iframe issues.
  pkceMethod: 'S256' as const, // Use the PKCE security flow.
};