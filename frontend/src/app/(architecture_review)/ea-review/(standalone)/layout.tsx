import { PageLayout } from '@/shared/components/layout/PageLayout';
import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function StandaloneLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('architecture_review')) {
    redirect('/forbidden');
  }

  return <PageLayout>{children}</PageLayout>;
}
