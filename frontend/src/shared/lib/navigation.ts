function isPathMatch(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + '/');
}

export function isRequesterPath(pathname: string): boolean {
  return pathname === '/' || pathname.startsWith('/request/') || pathname === '/ea-review/request/create';
}

export function isReviewerPath(pathname: string): boolean {
  return pathname === '/reviewer' || pathname.startsWith('/reviewer/');
}

export function isAdminPath(pathname: string): boolean {
  return pathname === '/admin'
    || pathname.startsWith('/admin/')
    || pathname === '/questionnaire-config'
    || pathname === '/concern-mapping-config'
    || pathname === '/architecture-artifact-catalog'
    || pathname === '/viewpoint-catalog'
    || pathname === '/concern-viewpoint-mapping'
    || pathname === '/viewpoint-artifact-mapping'
    || pathname === '/pact-concern-catalog'
    || pathname === '/ai-assessment'
    || pathname.startsWith('/ai-assessment/')
    || pathname === '/ai-models'
    || pathname.startsWith('/ai-models/')
    || pathname === '/ai-agents'
    || pathname.startsWith('/ai-agents/');
}

export function isSidebarItemActive(pathname: string, href: string): boolean {
  if (href === '/') {
    return isRequesterPath(pathname);
  }
  return isPathMatch(pathname, href);
}

export function isSidebarChildActive(pathname: string, href: string, search?: string): boolean {
  if (href === '/tech-stack') {
    return pathname === '/tech-stack';
  }
  return isPathMatch(pathname, href);
}
