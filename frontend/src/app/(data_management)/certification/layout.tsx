import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function CertificationLayout({ children }: { children: React.ReactNode }) {
  if (!isModuleEnabled('data_management')) {
    redirect('/forbidden');
  }

  return <>{children}</>;
}
