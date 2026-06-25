export const appConfig = {
  brandName: process.env.NEXT_PUBLIC_BRAND_NAME || 'AxisArch',
  appTitle: process.env.NEXT_PUBLIC_APP_TITLE || 'AxisArch',
  appSubtitle:
    process.env.NEXT_PUBLIC_APP_SUBTITLE || '',
  clusterBadge: process.env.NEXT_PUBLIC_CLUSTER_BADGE || '',
  appDescription:
    process.env.NEXT_PUBLIC_APP_DESCRIPTION || 'Enterprise Architecture Management Platform',
  logoSrc: process.env.NEXT_PUBLIC_LOGO_SRC || '/axisarch.png',
  logoAlt: process.env.NEXT_PUBLIC_LOGO_ALT || 'AxisArch',
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || '',
  supportContacts: (process.env.NEXT_PUBLIC_SUPPORT_CONTACTS || '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean),
  confluenceUrl: process.env.NEXT_PUBLIC_CONFLUENCE_URL || '',
  mspoUrl: process.env.NEXT_PUBLIC_MSPO_URL || '',
  keycloakDefaultUrl:
    process.env.NEXT_PUBLIC_KEYCLOAK_DEFAULT_URL || '',
  certificationTypes: [
    {
      label:
        process.env.NEXT_PUBLIC_CERT_TYPE_CLSA ||
        'CLSA',
      value:
        process.env.NEXT_PUBLIC_CERT_TYPE_CLSA ||
        'CLSA',
    },
    {
      label:
        process.env.NEXT_PUBLIC_CERT_TYPE_CLTA ||
        'CLTA',
      value:
        process.env.NEXT_PUBLIC_CERT_TYPE_CLTA ||
        'CLTA',
    },
  ],
};
