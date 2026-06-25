import { redirect } from 'next/navigation';
import { PageLayout } from '@/shared/components/layout/PageLayout';
import { isModuleEnabled } from '@/shared/modules/config';

export default function PlatformEngineeringLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('technology_stack_management')) {
    redirect('/forbidden');
  }

  return <PageLayout>{children}</PageLayout>;
}