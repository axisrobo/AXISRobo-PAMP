'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { ChevronDown, ChevronLeft } from 'lucide-react';
import { useState, useMemo } from 'react';
import clsx from 'clsx';
import { NavItem } from '@/shared/lib/constants';
import { useT } from '@/shared/lib/locale';
import { useAuth } from '@/shared/lib/auth-context';
import { isSidebarItemActive, isSidebarChildActive } from '@/shared/lib/navigation';
import { getEnabledSidebarItems } from '@/shared/modules/registry';
import { appConfig } from '@/shared/lib/app-config';

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  /** "inline" = normal aside sidebar, "drawer" = rendered inside a Drawer (no aside/sticky/collapse) */
  mode?: 'inline' | 'drawer';
}

function NavItemComponent({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const search = searchParams?.toString() ?? '';
  const t = useT();
  const hasChildren = item.children && item.children.length > 0;
  const currentPath = pathname ?? '';
  const isActive = isSidebarItemActive(currentPath, item.href);
  const isChildActive = hasChildren && item.children!.some(
    (child) => isSidebarChildActive(currentPath, child.href, search)
  );
  const [expanded, setExpanded] = useState(isActive || isChildActive);

  const Icon = item.icon;

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className={clsx(
            'w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded transition-colors',
            isActive || isChildActive
              ? 'bg-red-50 text-brand-primary font-medium'
              : 'text-text-primary hover:bg-gray-50'
          )}
        >
          <Icon className="w-4 h-4 flex-shrink-0" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left truncate">{t(item.label)}</span>
              <ChevronDown
                className={clsx(
                  'w-3.5 h-3.5 transition-transform flex-shrink-0',
                  expanded ? 'rotate-0' : '-rotate-90'
                )}
              />
            </>
          )}
        </button>
        {expanded && !collapsed && (
          <div className="ml-4 mt-0.5 space-y-0.5 border-l border-border-light pl-3">
            {item.children!.map((child) => {
              const isChildItemActive = isSidebarChildActive(currentPath, child.href, search);
              return (
                <Link
                  key={child.href}
                  href={child.href}
                  className={clsx(
                    'block px-3 py-2 text-sm rounded transition-colors',
                    isChildItemActive
                      ? 'text-brand-primary font-medium bg-red-50'
                      : 'text-text-secondary hover:text-text-primary hover:bg-gray-50'
                  )}
                >
                  {t(child.label)}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      className={clsx(
        'flex items-center gap-3 px-3 py-2.5 text-sm rounded transition-colors',
        isActive
          ? 'bg-red-50 text-brand-primary font-medium'
          : 'text-text-primary hover:bg-gray-50'
      )}
    >
      <Icon className="w-4 h-4 flex-shrink-0" />
      {!collapsed && <span className="truncate">{t(item.label)}</span>}
    </Link>
  );
}

/** Filter nav items based on user permissions and roles. */
function filterNavItems(
  items: NavItem[],
  hasPermission: (r: string, s?: string) => boolean,
  hasRole: (...roles: string[]) => boolean,
): NavItem[] {
  return items
    .filter((item) => {
      if (item.requiredResource && !hasPermission(item.requiredResource, item.requiredScope || 'read')) return false;
      // requiredRole: visible to ea_admin always, or to users with the specified role
      if (item.requiredRole && !hasRole('ea_admin', item.requiredRole)) return false;
      return true;
    })
    .map((item) => {
      if (!item.children) return item;
      const filteredChildren = filterNavItems(item.children, hasPermission, hasRole);
      // Hide parent if all children are filtered out
      if (filteredChildren.length === 0) return null;
      return { ...item, children: filteredChildren };
    })
    .filter(Boolean) as NavItem[];
}

export function Sidebar({ collapsed = false, onToggleCollapse, mode = 'inline' }: SidebarProps) {
  const t = useT();
  const { hasPermission, hasRole } = useAuth();
  const moduleEnabledItems = useMemo(() => getEnabledSidebarItems(), []);

  const visibleItems = useMemo(
    () => filterNavItems(moduleEnabledItems, hasPermission, hasRole),
    [hasPermission, hasRole, moduleEnabledItems]
  );

  const navContent = (
    <>
      <div className={clsx('px-3 pt-3 pb-2', collapsed && 'px-2')}>
        <Link href="/aict/cluster-map" className="block" title={appConfig.clusterBadge}>
          <div
            className={clsx(
              'rounded-md border border-brand-primary/30 bg-brand-primary/10 text-brand-primary text-xs font-semibold hover:bg-brand-primary/15 transition-colors',
              collapsed ? 'h-7 flex items-center justify-center' : 'px-2 py-1.5'
            )}
          >
            {collapsed ? 'C2' : appConfig.clusterBadge}
          </div>
        </Link>
      </div>
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {visibleItems.map((item) => (
          <NavItemComponent key={item.href + item.label} item={item} collapsed={collapsed} />
        ))}
      </nav>
    </>
  );

  // Drawer mode: no aside wrapper, no sticky, no collapse button
  if (mode === 'drawer') {
    return navContent;
  }

  return (
    <aside
      className={clsx(
        'relative h-[calc(100vh-56px)] bg-white border-r border-border-light flex flex-col transition-all duration-200 sticky top-14',
        collapsed ? 'w-14' : 'w-sidebar'
      )}
    >
      {navContent}

      {/* Floating collapse toggle button on right edge */}
      <button
        onClick={onToggleCollapse}
        title={collapsed ? t('Expand Sidebar') : t('Collapse Sidebar')}
        className="absolute -right-3 top-6 z-50 w-6 h-6 rounded-full bg-white border border-border-light shadow-sm flex items-center justify-center hover:bg-gray-50 transition-colors text-text-secondary"
      >
        <ChevronLeft
          className={clsx(
            'w-3.5 h-3.5 transition-transform duration-200',
            collapsed && 'rotate-180'
          )}
        />
      </button>
    </aside>
  );
}
