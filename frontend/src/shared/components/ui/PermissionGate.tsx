'use client';

import type { ReactNode } from 'react';
import { useAuth } from '@/shared/lib/auth-context';

interface PermissionGateProps {
  /** Resource name, e.g. "ea_request", "application" */
  resource: string;
  /** Scope, e.g. "read", "write", "execute". Default: "read" */
  scope?: string;
  /** Alternative: require one of these roles instead of resource/scope */
  roles?: string[];
  /** Content to render if the user has NO permission (default: nothing) */
  fallback?: ReactNode;
  children: ReactNode;
}

/**
 * Conditionally render children based on the current user's permissions.
 *
 * Usage:
 *   <PermissionGate resource="ea_request" scope="write">
 *     <button>Create EA Request</button>
 *   </PermissionGate>
 *
 *   <PermissionGate roles={["admin"]}>
 *     <AdminPanel />
 *   </PermissionGate>
 */
export function PermissionGate({
  resource,
  scope = 'read',
  roles,
  fallback = null,
  children,
}: PermissionGateProps) {
  const { hasPermission, hasRole, loading } = useAuth();

  // While loading auth, don't render gated content
  if (loading) return null;

  // Role-based check
  if (roles && roles.length > 0) {
    return hasRole(...roles) ? <>{children}</> : <>{fallback}</>;
  }

  // Permission-based check
  if (resource) {
    return hasPermission(resource, scope) ? <>{children}</> : <>{fallback}</>;
  }

  // No gate specified — render children
  return <>{children}</>;
}
