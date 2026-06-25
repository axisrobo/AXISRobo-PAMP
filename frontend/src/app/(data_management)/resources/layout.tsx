import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function ResourcesLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('data_management')) {
    redirect('/forbidden');
  }

  return <>{children}</>;
}
