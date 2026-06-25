'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';

const searchFields: SearchField[] = [
  { key: 'itcode', label: 'IT Code', type: 'text', placeholder: 'IT Code' },
  { key: 'name', label: 'Name', type: 'text', placeholder: 'Name' },
  { key: 'country', label: 'Country', type: 'text', placeholder: 'Country' },
  { key: 'tier1Org', label: 'Organization', type: 'text', placeholder: 'Organization' },
];

export default function ResourcesPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  // Add sort state
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const { data, isLoading } = useQuery({
    queryKey: ['resources', page, pageSize, filters, sortKey, sortDir],
    queryFn: () => api.get<any>('/resources', {
      page,
      pageSize,
      ...filters,
      sortField: sortKey || undefined,
      sortOrder: sortDir || undefined,
    }),
  });

  const columns: Column<any>[] = [
    { key: 'itcode', title: 'IT Code', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
    { key: 'name', title: 'Name', sortable: true },
    { key: 'email', title: 'Email', sortable: true },
    { key: 'workerType', title: 'Worker Type', sortable: true },
    { key: 'country', title: 'Country', sortable: true },
    { key: 'location', title: 'Location', sortable: true },
    { key: 'tier1Org', title: 'Organization', sortable: true },
  ];

  // Sort callback
  const handleSort = (key: string, direction: 'asc' | 'desc') => {
    setSortKey(key);
    setSortDir(direction);
    setPage(1);
  };

  return (
    <div className="p-6">
      <SearchForm
        fields={searchFields}
        onSearch={(v) => { setFilters(v); setPage(1); }}
        onReset={() => { setFilters({}); setPage(1); }}
      />

      <h2 className="text-base font-semibold text-text-primary mb-3">Resource Pool</h2>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="itcode"
        loading={isLoading}
        showColumnSettings
        onSort={handleSort}
        sortKey={sortKey}
        sortDirection={sortDir}
      />
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
