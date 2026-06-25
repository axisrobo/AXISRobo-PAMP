'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import MasterDataForm, { MasterRecord } from '@/features/tech-stack/components/master-data/MasterDataForm';
import { ArrowLeft } from 'lucide-react';

export default function EditMasterDataPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params?.id;

  const { data, isLoading, isError } = useQuery<MasterRecord>({
    queryKey: ['techStackMasterOne', id],
    queryFn: () => api.get<MasterRecord>(`/technology-stack/${id}`),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6 flex items-center gap-2 text-text-secondary text-sm">
        <span>Loading...</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-6">
        <button
          className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary mb-4"
          onClick={() => router.push('/tech-stack/master-data')}
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <p className="text-red-500 text-sm">Failed to load record. It may have been deleted.</p>
      </div>
    );
  }

  return <MasterDataForm initialValues={data} recordId={id} />;
}
