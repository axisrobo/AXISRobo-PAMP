import { PageLayout } from '@/shared/components/layout/PageLayout';
import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function ProjectsLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('project_management')) {
    redirect('/forbidden');
  }
  return <PageLayout>{children}</PageLayout>;
}
