'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';

const columns: Column<any>[] = [
  { key: 'name', title: 'Name', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'createdBy', title: 'Created By', sortable: true },
  { key: 'createdAt', title: 'Created At', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString() : '' },
];

export default function MasterDataCenterPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['masterData', 'dataCenters'],
    queryFn: () => api.get<any[]>('/master-data/data-centers'),
  });

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Data Center</h1>
      <DataTable columns={columns} data={data ?? []} rowKey="id" loading={isLoading} showColumnSettings />
      <div className="mt-2 text-xs text-text-secondary">{(data ?? []).length} data centers</div>
    </div>
  );
}
