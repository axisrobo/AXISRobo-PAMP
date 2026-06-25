'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { App, Input, Select } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { useAuth } from '@/shared/lib/auth-context';
import { Plus, Star } from 'lucide-react';
import Link from 'next/link';

const searchFields: SearchField[] = [
  { key: 'projectId', label: 'Project ID', type: 'text', placeholder: 'Project ID' },
  { key: 'name', label: 'Project Name', type: 'text', placeholder: 'Project Name' },
  { key: 'itCode', label: 'IT Code', type: 'text', placeholder: 'IT Code' },
  { key: 'requestStatus', label: 'Request Status', type: 'multiselect', options: [
    { label: 'Draft', value: 'Draft' },
    { label: 'Submitted', value: 'Submitted' },
    { label: 'In Progress', value: 'In Progress' },
    { label: 'Completed', value: 'Completed' },
  ]},
  { key: 'aiRelated', label: 'AI Related', type: 'multiselect', options: [
    { label: 'Yes', value: 'true' },
    { label: 'No', value: 'false' },
  ]},
];

export default function ProjectsPage() {
  const { message } = App.useApp();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, hasPermission, hasRole } = useAuth();
  const canWrite = hasPermission('project', 'write');
  const isAdmin = user?.permissions?.includes('*:*') ?? false;
  const isReviewer = hasRole('ea_reviewer');

  /** Check whether the current user can edit a specific project row. */
  const canEditRow = (row: any): boolean => {
    if (!canWrite) return false;
    // EA_Admin and EA_Reviewer can edit any row
    if (isAdmin || isReviewer) return true;
    // Project_Owner: user matches one of the project lead itcode fields
    const uid = user?.id?.toLowerCase();
    if (!uid) return false;
    return (
      uid === (row.pmItcode ?? '').toLowerCase() ||
      uid === (row.dtLeadItcode ?? '').toLowerCase() ||
      uid === (row.itLeadItcode ?? '').toLowerCase()
    );
  };
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [highFocus, setHighFocus] = useState(false);
  const [editingCell, setEditingCell] = useState<{ id: string; field: string; value: string } | null>(null);

  const queryKey = ['projects', page, pageSize, filters, sortKey, sortDir, highFocus];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => api.get<any>('/projects', {
      page,
      pageSize,
      ...filters,
      sortBy: sortKey || undefined,
      sortOrder: sortKey ? sortDir : undefined,
      ...(highFocus ? { favourite: true } : {}),
    }),
  });

  const updateProjectInline = useMutation({
    mutationFn: ({ projectId, payload }: { projectId: string; payload: Record<string, string | null> }) =>
      api.put<any>(`/projects/${encodeURIComponent(projectId)}`, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey });
      queryClient.invalidateQueries({ queryKey: ['project-detail', variables.projectId] });
    },
    onError: (e: any) => {
      message.error(e?.response?.data?.detail || e?.message || 'Failed to update project');
    },
  });

  const saveCell = (projectId: string, field: string, value: string) => {
    setEditingCell(null);
    updateProjectInline.mutate({ projectId, payload: { [field]: value || null } });
  };

  const changeFavourite = useMutation({
    mutationFn: ({ id, favourite }: { id: string; favourite: boolean }) =>
      api.post<any>('/projects/change-favourite', { id, favourite }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (e: any) => {
      message.error(e?.response?.data?.detail || e?.message || 'Failed to update favourite');
    },
  });

  const renderTextCell = (field: string, value: string, row: any) => {
    if (!canEditRow(row)) return value || '-';
    const cell = editingCell;
    if (cell !== null && cell.id === row.projectId && cell.field === field) {
      return (
        <Input
          autoFocus
          size="small"
          style={{ minWidth: 120 }}
          value={cell.value}
          onChange={(e) => setEditingCell({ id: cell!.id, field: cell!.field, value: e.target.value })}
          onBlur={() => saveCell(row.projectId, field, cell!.value)}
          onPressEnter={() => saveCell(row.projectId, field, cell!.value)}
        />
      );
    }
    return (
      <span
        style={{ cursor: 'text', display: 'block', minWidth: 80 }}
        title="Click to edit"
        onClick={(e) => { e.stopPropagation(); setEditingCell({ id: row.projectId, field, value: value || '' }); }}
      >
        {value || <span style={{ color: '#bfbfbf' }}>-</span>}
      </span>
    );
  };

  const renderSelectCell = (field: string, value: string, row: any, options: { label: string; value: string }[]) => {
    if (!canEditRow(row)) return value || '-';
    const cell = editingCell;
    if (cell !== null && cell.id === row.projectId && cell.field === field) {
      return (
        <Select
          autoFocus
          open
          size="small"
          style={{ minWidth: 90 }}
          value={cell!.value || undefined}
          options={options}
          allowClear
          onChange={(v) => { saveCell(row.projectId, field, v ?? ''); }}
          onDropdownVisibleChange={(open) => { if (!open) setEditingCell(null); }}
        />
      );
    }
    return (
      <span
        style={{ cursor: 'pointer', display: 'block', minWidth: 60 }}
        title="Click to edit"
        onClick={(e) => { e.stopPropagation(); setEditingCell({ id: row.projectId, field, value: value || '' }); }}
      >
        {value || <span style={{ color: '#bfbfbf' }}>-</span>}
      </span>
    );
  };

  const editableTitle = (label: string) => (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <EditOutlined style={{ fontSize: 11, color: '#8c8c8c' }} />{label}
    </span>
  );

  const AI_RELATED_OPTIONS = [
    { label: 'Yes', value: 'Yes' },
    { label: 'No', value: 'No' },
  ];

  const OVERALL_STATUS_OPTIONS = [
    { label: 'Draft', value: 'Draft' },
    { label: 'In progress', value: 'In progress' },
    { label: 'Approved', value: 'Approved' },
  ];

  const columns: Column<any>[] = [
    { key: 'favorite', title: 'High Focus', width: '80px', pinned: 'left', render: (_v, row) => {
      const isFav = row.favourite === true || row.favourite === 'true';
      return (
        <Star
          className={`w-4 h-4 cursor-pointer transition-colors ${
            isFav ? 'fill-yellow-400 text-yellow-400' : 'text-text-secondary hover:text-yellow-400'
          }`}
          onClick={(e) => { e.stopPropagation(); changeFavourite.mutate({ id: row.id, favourite: !isFav }); }}
        />
      );
    } },
    { key: 'projectId', title: 'Project ID', sortable: true, pinned: 'left', render: (v, row) => (
      <Link
        href={`/projects/${encodeURIComponent(row.projectId)}`}
        className="text-primary-blue font-medium hover:underline"
        onClick={(e) => e.stopPropagation()}
      >
        {v}
      </Link>
    ) },
    { key: 'name', title: 'Project Name', sortable: true },
    { key: 'pmName', title: 'PM', sortable: true },
    { key: 'dtLeadName', title: 'Biz Analyst', sortable: true },
    { key: 'itLeadName', title: 'IT Lead', sortable: true },
    { key: 'aiRelated', title: editableTitle('AI Related'), sortable: true, render: (v, row) => renderSelectCell('aiRelated', v, row, AI_RELATED_OPTIONS) },
    { key: 'comment', title: editableTitle('Comments'), render: (v, row) => renderTextCell('comment', v, row) },
    { key: 'overallStatus', title: editableTitle('Overall Status'), render: (v, row) => renderSelectCell('overallStatus', v, row, OVERALL_STATUS_OPTIONS) },
  ];

  return (
    <div className="p-6">
      <SearchForm
        fields={searchFields}
        onSearch={(v) => { setFilters(v); setPage(1); }}
        onReset={() => { setFilters({}); setPage(1); }}
        disableEnterSearch
      />

      {/* Action bar: New + High Focus toggle */}
      <div className="flex items-center mb-3 gap-3">
        <button
          onClick={() => router.push('/projects/new')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary-blue border border-primary-blue rounded hover:bg-blue-50"
        >
          <Plus className="w-3.5 h-3.5" />
          New
        </button>
        <label className="flex items-center gap-2 cursor-pointer">
          <div className={`relative w-10 h-5 rounded-full transition-colors ${highFocus ? 'bg-primary-blue' : 'bg-gray-300'}`} onClick={() => { setHighFocus(!highFocus); setPage(1); }}>
            <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${highFocus ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </div>
          <span className="text-sm text-text-secondary">High Focus</span>
        </label>
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="id"
        loading={isLoading}
        sortKey={sortKey}
        sortDirection={sortDir}
        onSort={(key, dir) => { setSortKey(key); setSortDir(dir); }}
        showColumnSettings
        exportConfig={{ entity: 'projects', params: filters }}
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
