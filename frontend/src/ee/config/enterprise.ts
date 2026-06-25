/**
 * Enterprise Edition configuration.
 * These values override OSS defaults when EE mode is enabled.
 * Set NEXT_PUBLIC_EE_ENABLED=true to activate.
 */
export const eeConfig = {
  enabled: process.env.NEXT_PUBLIC_EE_ENABLED === "true",

  /** Enterprise SSO configuration */
  keycloak: {
    url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || "",
    realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "master",
    clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || "",
  },

  /** Enterprise external links */
  links: {
    confluence: process.env.NEXT_PUBLIC_CONFLUENCE_URL || "",
    mspo: process.env.NEXT_PUBLIC_MSPO_URL || "",
  },

  /** Enterprise support */
  support: {
    email: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "",
    contacts: process.env.NEXT_PUBLIC_SUPPORT_CONTACTS || "",
  },
};
