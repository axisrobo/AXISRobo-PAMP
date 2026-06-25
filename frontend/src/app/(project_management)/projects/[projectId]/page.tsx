/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useMemo, useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Trash2, PlusCircle, X, Pencil } from 'lucide-react';
import { message, Modal, Input, Button, Radio, Pagination as AntPagination, Spin } from 'antd';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { useAuth } from '@/shared/lib/auth-context';

type ProjectDetail = {
  projectId: string;
  name?: string;
  type?: string;
  objectives?: string;
  status?: string;
  startDate?: string;
  goLiveDate?: string;
  duration?: string | number;
  aiRelated?: string;
  pmName?: string;
  pmItcode?: string;
  dtLeadName?: string;
  dtLeadItcode?: string;
  itLeadName?: string;
  itLeadItcode?: string;
  comment?: string;
  overallStatus?: string;
};

type ProjectTask = {
  id: string;
  name?: string;
  assignee?: string;
  approvalStatus?: string;
  approvalDate?: string;
  status?: string;
  comment?: string;
  description?: string;
  createdAt?: string;
};

type ProjectApplication = {
  id: string;
  applicationId?: string;
  name?: string;
  fullName?: string;
  itOwner?: string;
  currentStatus?: string;
};

interface CmdbApp {
  appId: string;
  name?: string;
  appFullName?: string;
  appItOwner?: string;
  status?: string;
}

function showValue(v: unknown): string {
  if (v === null || v === undefined || v === '') return '-';
  return String(v);
}

function fmtDate(v?: string): string {
  if (!v) return '-';
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return v;
  return d.toISOString().slice(0, 10);
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white border border-border-light rounded-lg p-4 md:p-5">
      <h2 className="text-base font-semibold text-text-primary mb-4">{title}</h2>
      {children}
    </section>
  );
}

function KV({ label, value }: { label: string; value?: unknown }) {
  return (
    <div className="grid grid-cols-[160px_1fr] items-start gap-2 py-1.5">
      <span className="text-text-secondary">{label}:</span>
      <span className="text-text-primary">{showValue(value)}</span>
    </div>
  );
}

// ── CMDB Picker Modal ───────────────────────────────────────────

function CmdbPickerModal({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (app: CmdbApp) => void;
}) {
  const [appIdInput, setAppIdInput] = useState('');
  const [appNameInput, setAppNameInput] = useState('');
  const [items, setItems] = useState<CmdbApp[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<{ appId: string; appName: string }>({ appId: '', appName: '' });
  const [selected, setSelected] = useState<CmdbApp | null>(null);

  useEffect(() => {
    fetchData({ appId: '', appName: '' }, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchData(filter: { appId: string; appName: string }, targetPage: number) {
    setLoading(true);
    try {
      const params: Record<string, any> = { page: targetPage, pageSize };
      if (filter.appId) params.appId = filter.appId;
      if (filter.appName) params.name = filter.appName;
      const res = await api.get<any>('/cmdb', params);
      setItems(res.data ?? []);
      setTotal(res.total ?? 0);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    const filter = { appId: appIdInput.trim(), appName: appNameInput.trim() };
    setActiveFilter(filter);
    setSelected(null);
    setPage(1);
    fetchData(filter, 1);
  }

  function handleReset() {
    setAppIdInput('');
    setAppNameInput('');
    const empty = { appId: '', appName: '' };
    setActiveFilter(empty);
    setSelected(null);
    setPage(1);
    fetchData(empty, 1);
  }

  function handlePageChange(newPage: number) {
    setPage(newPage);
    fetchData(activeFilter, newPage);
  }

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-[900px] max-w-[95vw] flex flex-col" style={{ maxHeight: '80vh' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-base font-semibold text-gray-800">Select Application from CMDB</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search bar */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex items-center gap-3 flex-wrap">
            <Input
              placeholder="Application ID"
              value={appIdInput}
              onChange={e => setAppIdInput(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 180 }}
              allowClear
            />
            <Input
              placeholder="Application Name"
              value={appNameInput}
              onChange={e => setAppNameInput(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 220 }}
              allowClear
            />
            <Button type="primary" onClick={handleSearch}>Search</Button>
            <Button onClick={handleReset}>Reset</Button>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto px-6 py-3">
          {loading ? (
            <div className="flex items-center justify-center py-12"><Spin /></div>
          ) : items.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-gray-400 text-sm">No results found</div>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="w-8 px-3 py-2.5"></th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Application ID</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Name</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Full Name</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">IT Owner</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.appId}
                    className={`border-b border-gray-100 cursor-pointer hover:bg-blue-50 transition-colors ${selected?.appId === item.appId ? 'bg-blue-50' : ''}`}
                    onClick={() => setSelected(item)}
                  >
                    <td className="px-3 py-2.5 text-center">
                      <Radio checked={selected?.appId === item.appId} onChange={() => setSelected(item)} />
                    </td>
                    <td className="px-3 py-2.5 text-gray-800">{item.appId}</td>
                    <td className="px-3 py-2.5 text-gray-700">{item.name}</td>
                    <td className="px-3 py-2.5 text-gray-700">{item.appFullName || item.name}</td>
                    <td className="px-3 py-2.5 text-gray-600">{item.appItOwner || '-'}</td>
                    <td className="px-3 py-2.5 text-gray-600">{item.status || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className="px-6 py-3 border-t bg-gray-50 flex items-center justify-between">
            <span className="text-sm text-gray-500">Total {total} Items</span>
            <AntPagination
              current={page}
              total={total}
              pageSize={pageSize}
              onChange={handlePageChange}
              showSizeChanger={false}
              size="small"
            />
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" disabled={!selected} onClick={() => selected && onConfirm(selected)}>OK</Button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page Component ─────────────────────────────────────────

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.permissions?.includes('*:*') ?? false;
  const isReviewer = user?.roles?.includes('ea_reviewer') ?? false;
  const projectId = decodeURIComponent(params?.projectId || '');

  const [showCmdbPicker, setShowCmdbPicker] = useState(false);

  const projectQuery = useQuery({
    queryKey: ['project-detail', projectId],
    queryFn: () => api.get<ProjectDetail>(`/projects/${encodeURIComponent(projectId)}`),
    enabled: !!projectId,
  });

  const project = projectQuery.data;

  // Determine whether the current user can edit this project (admin or project owner)
  const isProjectOwner = useMemo(() => {
    if (!user || !project) return false;
    const uid = user.id?.toLowerCase();
    if (!uid) return false;
    return (
      uid === (project.pmItcode ?? '').toLowerCase() ||
      uid === (project.dtLeadItcode ?? '').toLowerCase() ||
      uid === (project.itLeadItcode ?? '').toLowerCase()
    );
  }, [user, project]);

  const canEdit = isAdmin || isReviewer || isProjectOwner;

  // ── Delete project mutation ────────────────────────────────────

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/projects/${encodeURIComponent(projectId)}`),
    onSuccess: () => {
      message.success('Project deleted successfully');
      router.push('/projects');
    },
    onError: (e: any) => {
      message.error(e?.response?.data?.detail || e?.message || 'Failed to delete project');
    },
  });

  const handleDelete = () => {
    Modal.confirm({
      title: 'Delete Project',
      content: `Are you sure you want to delete project "${projectId}"? This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: () => deleteMutation.mutateAsync(),
    });
  };

  // ── Sub-queries ────────────────────────────────────────────────

  const tasksQuery = useQuery({
    queryKey: ['project-sub-tasks', projectId],
    queryFn: () => api.get<ProjectTask[]>(`/projects/${encodeURIComponent(projectId)}/tasks`),
    enabled: !!projectId,
  });

  const applicationsQuery = useQuery({
    queryKey: ['project-applications', projectId],
    queryFn: () => api.get<ProjectApplication[]>(`/projects/${encodeURIComponent(projectId)}/applications`),
    enabled: !!projectId,
  });

  // ── Application mutations ──────────────────────────────────────

  const addAppMutation = useMutation({
    mutationFn: (appId: string) =>
      api.post<any>(`/projects/${encodeURIComponent(projectId)}/applications`, { appId }),
    onSuccess: () => {
      message.success('Application added successfully');
      queryClient.invalidateQueries({ queryKey: ['project-applications', projectId] });
      setShowCmdbPicker(false);
    },
    onError: (e: any) => {
      message.error(e?.response?.data?.detail || e?.message || 'Failed to add application');
    },
  });

  const removeAppMutation = useMutation({
    mutationFn: (appId: string) =>
      api.delete(`/projects/${encodeURIComponent(projectId)}/applications/${encodeURIComponent(appId)}`),
    onSuccess: () => {
      message.success('Application removed successfully');
      queryClient.invalidateQueries({ queryKey: ['project-applications', projectId] });
    },
    onError: (e: any) => {
      message.error(e?.response?.data?.detail || e?.message || 'Failed to remove application');
    },
  });

  const handleRemoveApp = (appId: string) => {
    Modal.confirm({
      title: 'Remove Application',
      content: `Are you sure you want to remove application "${appId}" from this project?`,
      okText: 'Remove',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: () => removeAppMutation.mutateAsync(appId),
    });
  };

  // ── Column definitions ─────────────────────────────────────────

  const subTaskColumns: Column<ProjectTask>[] = useMemo(
    () => [
      { key: 'name', title: 'Name' },
      { key: 'assignee', title: 'Assignee' },
      { key: 'approvalStatus', title: 'Approval Status' },
      { key: 'approvalDate', title: 'Approval Date', render: (v) => fmtDate(v) },
      { key: 'status', title: 'Status', render: (v) => v ? <StatusBadge status={String(v)} /> : '-' },
      { key: 'comment', title: 'Comment' },
      { key: 'description', title: 'Description' },
      { key: 'createdAt', title: 'Created At', render: (v) => fmtDate(v) },
    ],
    [],
  );

  const applicationColumns: Column<ProjectApplication>[] = useMemo(
    () => {
      const cols: Column<ProjectApplication>[] = [
        { key: 'applicationId', title: 'Application ID' },
        { key: 'name', title: 'Name' },
        { key: 'fullName', title: 'Full Name' },
        { key: 'itOwner', title: 'IT Owner' },
        { key: 'currentStatus', title: 'Current Status', render: (v) => v ? <StatusBadge status={String(v)} /> : '-' },
      ];
      if (canEdit) {
        cols.push({
          key: 'operation' as any,
          title: 'Operation',
          width: '100px',
          render: (_v, row) => (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (row.applicationId) handleRemoveApp(row.applicationId);
              }}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              Delete
            </button>
          ),
        });
      }
      return cols;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [canEdit],
  );

  // ── Render ─────────────────────────────────────────────────────

  if (projectQuery.isError) {
    return (
      <div className="p-6">
        <button onClick={() => router.push('/projects')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-blue mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="bg-white border border-red-200 rounded-lg p-4 text-red-600 text-sm">Failed to load project detail.</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => router.push('/projects')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-blue transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h1 className="text-lg font-semibold text-text-primary">Project Detail</h1>
        <div className="ml-auto flex items-center gap-2">
          {canEdit && (
            <button
              onClick={() => router.push(`/projects/${encodeURIComponent(projectId)}/edit`)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-primary-blue rounded hover:bg-primary-blue-hover"
            >
              <Pencil className="w-3.5 h-3.5" />
              Change
            </button>
          )}
          {isAdmin && (
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </button>
          )}
        </div>
      </div>

      <Section title="General Data">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
          <div>
            <KV label="Project ID" value={project?.projectId || projectId} />
            <KV label="Project Name" value={project?.name} />
            <KV label="Request Type" value={project?.type} />
            <KV label="Objectives" value={project?.objectives} />
          </div>
          <div>
            <div className="grid grid-cols-[160px_1fr] items-start gap-2 py-1.5">
              <span className="text-text-secondary">Status:</span>
              <span>{project?.status ? <StatusBadge status={project.status} /> : '-'}</span>
            </div>
            <KV label="Start Date" value={fmtDate(project?.startDate)} />
            <KV label="Go Live Date" value={fmtDate(project?.goLiveDate)} />
            <KV label="Duration (Months)" value={project?.duration} />
            <KV label="AI Related" value={project?.aiRelated} />
          </div>
        </div>
      </Section>

      <Section title="Persons Responsible">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
          <div>
            <KV label="PM" value={project?.pmName} />
            <KV label="Biz Analyst" value={project?.dtLeadName} />
            <KV label="Comments" value={project?.comment} />
          </div>
          <div>
            <KV label="IT Lead" value={project?.itLeadName} />
          </div>
        </div>
      </Section>

      <Section title="EA Review">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 mb-3">
          <div>
            <KV label="Risk Status" value={project?.overallStatus} />
          </div>
          <div>
            <KV label="Overall Status" value={project?.overallStatus} />
          </div>
        </div>

        <h3 className="text-sm font-semibold text-text-primary mt-2 mb-2">Sub Tasks</h3>
        <DataTable
          columns={subTaskColumns}
          data={tasksQuery.data ?? []}
          rowKey="id"
          loading={tasksQuery.isLoading}
          emptyText="No Data"
        />

        <div className="flex items-center gap-2 mt-6 mb-2">
          <h3 className="text-sm font-semibold text-text-primary">Applications</h3>
          {canEdit && (
            <button
              onClick={() => setShowCmdbPicker(true)}
              className="text-primary-blue hover:text-blue-700 transition-colors"
              title="Add Application"
            >
              <PlusCircle className="w-4.5 h-4.5" />
            </button>
          )}
        </div>
        <DataTable
          columns={applicationColumns}
          data={applicationsQuery.data ?? []}
          rowKey="id"
          loading={applicationsQuery.isLoading}
          emptyText="No Data"
        />
      </Section>

      {showCmdbPicker && (
        <CmdbPickerModal
          onClose={() => setShowCmdbPicker(false)}
          onConfirm={(app) => addAppMutation.mutate(app.appId)}
        />
      )}
    </div>
  );
}
