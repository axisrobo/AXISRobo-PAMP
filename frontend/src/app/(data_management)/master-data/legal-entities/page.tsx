'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';

const columns: Column<any>[] = [
  { key: 'companyCode', title: 'Company Code', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'appId', title: 'Application ID', sortable: true },
  { key: 'createdAt', title: 'Created At', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '' },
];

export default function MasterDataLegalEntitiesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['masterData', 'legalEntities'],
    queryFn: () => api.get<any[]>('/master-data/legal-entities'),
  });

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Legal Entities</h1>
      <DataTable columns={columns} data={data ?? []} rowKey="id" loading={isLoading} showColumnSettings />
      <div className="mt-2 text-xs text-text-secondary">{(data ?? []).length} legal entities</div>
    </div>
  );
}
