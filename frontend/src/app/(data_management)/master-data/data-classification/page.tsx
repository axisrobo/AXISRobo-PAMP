'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';

const columns: Column<any>[] = [
  { key: 'code', title: 'Code', sortable: true },
  { key: 'nameEn', title: 'Name (EN)', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'nameZh', title: 'Name (ZH)', sortable: true },
  { key: 'method', title: 'Method', sortable: true },
  { key: 'level', title: 'Level', sortable: true },
  { key: 'parent', title: 'Parent', sortable: true },
  { key: 'status', title: 'Status', sortable: true },
];

export default function MasterDataClassificationPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['masterData', 'dataClassification'],
    queryFn: () => api.get<any[]>('/master-data/data-classification'),
  });

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Data Classification</h1>
      <DataTable columns={columns} data={data ?? []} rowKey="id" loading={isLoading} showColumnSettings />
      <div className="mt-2 text-xs text-text-secondary">{(data ?? []).length} classification items</div>
    </div>
  );
}
