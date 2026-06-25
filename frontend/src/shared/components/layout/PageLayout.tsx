'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Drawer } from 'antd';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { LoginGate } from '@/shared/components/ui/LoginGate';
import { useMediaQuery } from '@/shared/lib/useMediaQuery';

export function PageLayout({ children }: { children: React.ReactNode }) {
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();

  // Auto-close Drawer on navigation
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  return (
    <LoginGate>
      <div className="min-h-screen bg-bg-gray">
        <Header onMenuClick={isDesktop ? undefined : () => setDrawerOpen((v) => !v)} />
        <div className="flex">
          {isDesktop ? (
            <Sidebar
              collapsed={sidebarCollapsed}
              onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
          ) : (
            <Drawer
              placement="left"
              open={drawerOpen}
              onClose={() => setDrawerOpen(false)}
              size={260}
              styles={{ body: { padding: 0 } }}
              closable={false}
            >
              <Sidebar mode="drawer" />
            </Drawer>
          )}
          <main className="flex-1 min-h-[calc(100vh-56px)] overflow-x-auto">
            {children}
          </main>
        </div>
      </div>
    </LoginGate>
  );
}
