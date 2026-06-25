'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { ToastProvider } from '@/shared/components/ui/Toast';
import { LocaleProvider } from '@/shared/lib/locale';
import { AuthProvider } from '@/shared/lib/auth-context';
import { AuthGuard } from '@/shared/lib/AuthGuard';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LocaleProvider>
          <ToastProvider>
            <AuthGuard>{children}</AuthGuard>
          </ToastProvider>
        </LocaleProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
