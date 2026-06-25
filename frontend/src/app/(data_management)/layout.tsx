import { redirect } from 'next/navigation';
import { PageLayout } from '@/shared/components/layout/PageLayout';
import { isModuleEnabled } from '@/shared/modules/config';

export default function DataManagementLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('data_management')) {
    redirect('/forbidden');
  }

  return <PageLayout>{children}</PageLayout>;
}