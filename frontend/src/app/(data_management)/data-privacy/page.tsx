'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { Shield, Database } from 'lucide-react';

type TabKey = 'applications' | 'dataClassification';

const tabs: { key: TabKey; label: string; icon: any }[] = [
  { key: 'applications', label: 'Applications', icon: Database },
  { key: 'dataClassification', label: 'Data Classification', icon: Shield },
];

const appSearchFields: SearchField[] = [
  { key: 'search', label: 'Search', type: 'text', placeholder: 'Application name or ID' },
];

const appColumns: Column<any>[] = [
  { key: 'appId', title: 'App ID', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'appName', title: 'Application Name', sortable: true },
  { key: 'appStatus', title: 'Status', sortable: true },
  { key: 'organization', title: 'Organization', sortable: true },
  { key: 'businessCriticality', title: 'Business Criticality', sortable: true },
];

const classificationColumns: Column<any>[] = [
  { key: 'code', title: 'Code', sortable: true },
  { key: 'nameEn', title: 'Name (EN)', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
  { key: 'nameZh', title: 'Name (ZH)', sortable: true },
  { key: 'method', title: 'Method', sortable: true },
  { key: 'level', title: 'Level', sortable: true },
  { key: 'status', title: 'Status', sortable: true },
];

export default function DataPrivacyPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('applications');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const { data: apps, isLoading: loadingApps } = useQuery({
    queryKey: ['privacyApps', page, pageSize, filters],
    queryFn: () => api.get<any>('/applications', { page, pageSize, ...filters }),
    enabled: activeTab === 'applications',
  });

  const { data: classification, isLoading: loadingClassification } = useQuery({
    queryKey: ['privacyClassification'],
    queryFn: () => api.get<any[]>('/master-data/data-classification'),
    enabled: activeTab === 'dataClassification',
  });

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-4">
        <Shield className="w-6 h-6 text-primary-blue" />
        <h1 className="text-lg font-semibold text-text-primary">Data Privacy & Protection</h1>
      </div>

      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4">
        <p className="text-sm text-blue-800">
          Manage data privacy and protection policies for applications. View data classification, data residency requirements, and compliance status.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-border-light mb-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary-blue text-primary-blue'
                  : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'applications' && (
        <>
          <SearchForm
            fields={appSearchFields}
            onSearch={(v) => { setFilters(v); setPage(1); }}
            onReset={() => { setFilters({}); setPage(1); }}
          />
          <DataTable columns={appColumns} data={apps?.data ?? []} rowKey="id" loading={loadingApps} showColumnSettings />
          {apps && (
            <Pagination
              currentPage={page}
              totalPages={apps.totalPages || 1}
              totalItems={apps.total || 0}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
            />
          )}
        </>
      )}

      {activeTab === 'dataClassification' && (
        <>
          <DataTable columns={classificationColumns} data={classification ?? []} rowKey="id" loading={loadingClassification} showColumnSettings />
          <div className="mt-2 text-xs text-text-secondary">{(classification ?? []).length} classification items</div>
        </>
      )}
    </div>
  );
}
