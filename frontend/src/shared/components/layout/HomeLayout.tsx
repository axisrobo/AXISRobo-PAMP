'use client';

import { Header } from './Header';
import { Footer } from './Footer';
import { LoginGate } from '@/shared/components/ui/LoginGate';

export function HomeLayout({ children }: { children: React.ReactNode }) { // Used as RequesterLayout
  return (
    <LoginGate>
      <div className="min-h-screen bg-white flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </div>
    </LoginGate>
  );
}
