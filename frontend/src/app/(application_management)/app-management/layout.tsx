import { PageLayout } from '@/shared/components/layout/PageLayout';
import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function AppManagementLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('application_management')) {
    redirect('/forbidden');
  }
  return <PageLayout>{children}</PageLayout>;
}
