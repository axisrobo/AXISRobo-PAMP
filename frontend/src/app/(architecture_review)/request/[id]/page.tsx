import { HomeLayout } from '@/shared/components/layout/HomeLayout';
import { RequestDetailView } from '@/features/review/stages/review';
import { redirect } from 'next/navigation';
import { isModuleEnabled } from '@/shared/modules/config';

export default function StandaloneRequestDetailPage() {
  if (!isModuleEnabled('architecture_review')) {
    redirect('/forbidden');
  }

  return (
    <HomeLayout>
      <div className="max-w-7xl mx-auto">
        <RequestDetailView />
      </div>
    </HomeLayout>
  );
}
