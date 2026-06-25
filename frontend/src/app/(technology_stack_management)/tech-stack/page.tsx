'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { Plus, HelpCircle } from 'lucide-react';
import { useAuth } from '@/shared/lib/auth-context';
import { ApplicationTechStackModal } from '@/features/tech-stack/components/lifecycle/ApplicationTechStackModal';
import { CmdbPickerModal } from '@/features/tech-stack/components/lifecycle/CmdbPickerModal';

const searchFields: SearchField[] = [
  { key: 'applicationId', label: 'Application ID', type: 'text', placeholder: 'Application ID' },
  { key: 'applicationName', label: 'Application Name', type: 'text', placeholder: 'Application Name' },
  { key: 'applicationOwner', label: 'Application Owner', type: 'text', placeholder: 'Application Owner' },
  { key: 'lifecycleStatus', label: 'Lifecycle Status', type: 'multiselect', options: [
    { label: 'Active', value: 'Active' },
    { label: 'EOL', value: 'EOL' },
  ]},
];

export default function LifecycleManagementPage() {
  const { hasPermission } = useAuth();
  const canWriteTechStack = hasPermission('tech_stack_lifecycle', 'write');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  // Add sort state
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  // Drawer / picker state
  const [pickerOpen, setPickerOpen] = useState(false);
  const [drawer, setDrawer] = useState<{ open: boolean; mode: 'new' | 'detail'; appId?: string; prefillData?: any }>({
    open: false,
    mode: 'new',
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['lifecycleManagement', page, pageSize, filters, sortKey, sortDir],
    queryFn: () => api.get<any>('/technology-stack/lifecycle', {
      page,
      pageSize,
      ...filters,
      sortField: sortKey || undefined,
      sortOrder: sortDir || undefined,
    }),
  });

  const columns: Column<any>[] = [
    {
      key: 'applicationId',
      title: 'Application ID',
      sortable: true,
      render: (v) => (
        <button
          className="text-primary-blue font-medium hover:underline"
          onClick={() => setDrawer({ open: true, mode: 'detail', appId: v })}
        >
          {v}
        </button>
      ),
    },
    { key: 'applicationName', title: 'Application Name', sortable: true },
    { key: 'applicationOwnership', title: 'Application Ownership', sortable: true },
    { key: 'applicationClassification', title: 'Application Classification', sortable: true },
    { key: 'functionValueChain', title: 'Function (Value Chain)', sortable: true },
    { key: 'applicationOwner', title: 'Application Owner', sortable: true },
    { key: 'lifecycleStatus', title: 'Lifecycle Status', sortable: true },
  ];

  // Sort callback
  const handleSort = (key: string, direction: 'asc' | 'desc') => {
    setSortKey(key);
    setSortDir(direction);
    setPage(1);
  };

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Technology Stack Lifecycle Management</h1>

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4">
        {canWriteTechStack && (
          <button
            onClick={() => setPickerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary-blue border border-primary-blue rounded hover:bg-blue-50"
          >
            <Plus className="w-3.5 h-3.5" />
            Select Application
          </button>
        )}
        <button className="text-text-secondary hover:text-text-primary">
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>

      <SearchForm
        fields={searchFields}
        onSearch={(v) => { setFilters(v); setPage(1); }}
        onReset={() => { setFilters({}); setPage(1); }}
      />

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="id"
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

      {/* CMDB Picker — opens first to select an application */}
      {pickerOpen && (
        <CmdbPickerModal
          onClose={() => setPickerOpen(false)}
          onConfirm={(app) => {
            setPickerOpen(false);
            setDrawer({ open: true, mode: 'new', prefillData: app });
          }}
        />
      )}

      {/* Application Tech Stack Drawer */}
      {drawer.open && (
        <ApplicationTechStackModal
          mode={drawer.mode}
          appId={drawer.appId}
          prefillData={drawer.prefillData}
          onClose={() => setDrawer({ open: false, mode: 'new' })}
          onSaved={() => refetch()}
        />
      )}
    </div>
  );
}
