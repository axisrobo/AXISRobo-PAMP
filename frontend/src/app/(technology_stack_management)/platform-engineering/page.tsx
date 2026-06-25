'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { Server } from 'lucide-react';

const searchFields: SearchField[] = [
  { key: 'search', label: 'Search', type: 'text', placeholder: 'Application name or ID' },
];

const columns: Column<any>[] = [
  { key: 'appId', title: 'App ID', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'appName', title: 'Application Name', sortable: true },
  { key: 'appStatus', title: 'Status', sortable: true },
  { key: 'organization', title: 'Organization', sortable: true },
  { key: 'businessCriticality', title: 'Business Criticality', sortable: true },
  { key: 'appType', title: 'App Type', sortable: true },
];

export default function PlatformEngineeringPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['platformApps', page, pageSize, filters],
    queryFn: () => api.get<any>('/applications', { page, pageSize, ...filters }),
  });

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-4">
        <Server className="w-6 h-6 text-primary-blue" />
        <h1 className="text-lg font-semibold text-text-primary">Platform Engineering</h1>
      </div>

      <div className="bg-purple-50 border border-purple-100 rounded-lg p-4 mb-4">
        <p className="text-sm text-purple-800">
          Platform engineering overview of applications, infrastructure components, and deployment environments.
        </p>
      </div>

      <SearchForm
        fields={searchFields}
        onSearch={(v) => { setFilters(v); setPage(1); }}
        onReset={() => { setFilters({}); setPage(1); }}
      />

      <DataTable columns={columns} data={data?.data ?? []} rowKey="id" loading={isLoading} showColumnSettings />
      {data && (
        <Pagination
          currentPage={page}
          totalPages={data.totalPages || 1}
          totalItems={data.total || 0}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        />
      )}
    </div>
  );
}
