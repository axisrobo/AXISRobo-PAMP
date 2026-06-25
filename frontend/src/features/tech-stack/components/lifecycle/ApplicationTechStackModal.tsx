/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, Pencil, Trash2, ChevronLeft } from 'lucide-react';
import { Input, Select, Button, Pagination, Modal } from 'antd';
import dayjs from 'dayjs';
import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';
import { RiskLevelBadge } from '@/shared/components/ui/RiskLevelBadge';
import { CatalogItemModal } from './CatalogItemModal';
import { ResourcePoolPickerModal } from './ResourcePoolPickerModal';

type ModalMode = 'new' | 'detail';
type ActiveTab = 'catalog' | 'team' | 'log';

interface ApplicationTechStackModalProps {
  mode: ModalMode;
  appId?: string;       // required when mode='detail'
  prefillData?: any;    // pre-selected CMDB app data when mode='new'
  onClose: () => void;
  onSaved?: () => void;
}

export function ApplicationTechStackModal({ mode, appId: initialAppId, prefillData, onClose, onSaved }: ApplicationTechStackModalProps) {
  const { user, hasPermission } = useAuth();
  const canWrite = hasPermission('tech_stack_master', 'write');
  const isAdmin = user?.permissions?.includes('*:*') ?? false;
  const queryClient = useQueryClient();
  const [modal, contextHolder] = Modal.useModal();

  // ── State ─────────────────────────────────────────────────────
  const [currentMode, setCurrentMode] = useState<ModalMode>(mode);
  const [currentAppId, setCurrentAppId] = useState<string>(initialAppId ?? '');
  const [activeTab, setActiveTab] = useState<ActiveTab>('catalog');

  // General Data (new mode) — initialised from prefillData passed by parent picker
  const [generalData] = useState<any>(prefillData ?? null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  // Catalog filter
  const [catalogFilters, setCatalogFilters] = useState({ category: '', subCategory: '', component: '', useStatus: '' });
  const [catalogPage, setCatalogPage] = useState(1);
  const [catalogItemModal, setCatalogItemModal] = useState<{ open: boolean; item?: any }>({ open: false });
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; label: string } | null>(null);
  const [checkingMsg, setCheckingMsg] = useState('');
  const [checkingLoading, setCheckingLoading] = useState(false);

  // Add Team Member
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [addMemberLoading, setAddMemberLoading] = useState(false);

  // Changed Log pagination
  const [logPage, setLogPage] = useState(1);

  const appIdForQueries = currentMode === 'detail' ? currentAppId : undefined;

  // ── Queries ───────────────────────────────────────────────────

  const { data: detailData } = useQuery({
    queryKey: ['appTechDetail', appIdForQueries],
    queryFn: () => api.get<any>(`/technology-stack/apps/${appIdForQueries}`),
    enabled: !!appIdForQueries,
  });

  const { data: catalogData, isLoading: catalogLoading } = useQuery({
    queryKey: ['appCatalog', appIdForQueries, catalogPage, catalogFilters],
    queryFn: () =>
      api.get<any>(`/technology-stack/apps/${appIdForQueries}/catalog`, {
        page: catalogPage,
        pageSize: 10,
        ...Object.fromEntries(Object.entries(catalogFilters).filter(([, v]) => v)),
      }),
    enabled: !!appIdForQueries && activeTab === 'catalog',
  });

  const { data: categoryData } = useQuery({
    queryKey: ['techStackCategoryOptions'],
    queryFn: () => api.get<any>('/technology-stack/categories'),
    enabled: activeTab === 'catalog',
  });

  const categoryOptions = useMemo(
    () => (categoryData?.categories ?? []).map((o: any) => ({ label: o.label, value: o.value })),
    [categoryData]
  );

  const subCategoryOptions = useMemo(() => {
    const all = (categoryData?.subCategories ?? []) as Array<{ category: string; label: string; value: string }>;
    if (!catalogFilters.category) {
      return [];
    }
    return all
      .filter((o) => o.category === catalogFilters.category)
      .map((o) => ({ label: o.label, value: o.value }));
  }, [categoryData, catalogFilters.category]);

  useEffect(() => {
    if (!catalogFilters.subCategory) return;
    const valid = subCategoryOptions.some((o) => o.value === catalogFilters.subCategory);
    if (!valid) {
      setCatalogFilters((f) => ({ ...f, subCategory: '' }));
    }
  }, [catalogFilters.subCategory, subCategoryOptions]);

  const { data: teamData } = useQuery({
    queryKey: ['appTeamMembers', appIdForQueries],
    queryFn: () => api.get<any>(`/technology-stack/apps/${appIdForQueries}/team-members`),
    enabled: !!appIdForQueries,
  });

  const { data: logData } = useQuery({
    queryKey: ['appOperateLog', appIdForQueries, logPage],
    queryFn: () => api.get<any>(`/technology-stack/apps/${appIdForQueries}/operate-log`, { page: logPage, pageSize: 20 }),
    enabled: !!appIdForQueries && activeTab === 'log',
  });

  // ── Register app ──────────────────────────────────────────────

  async function handleSaveNew() {
    if (!generalData) { setSaveError('Please search for an application first'); return; }
    setSaving(true);
    setSaveError('');
    try {
      await api.post<any>('/technology-stack/apps', { appId: generalData.appId });
      setCurrentAppId(generalData.appId);
      setCurrentMode('detail');
      onSaved?.();
      queryClient.invalidateQueries({ queryKey: ['lifecycleManagement'] });
    } catch (err: any) {
      setSaveError(err?.message ?? 'Registration failed');
    } finally {
      setSaving(false);
    }
  }

  // ── Delete app ────────────────────────────────────────────────

  async function handleDeleteApp() {
    if (!currentAppId) return;
    try {
      await api.delete<any>(`/technology-stack/apps/${currentAppId}`);
      onSaved?.();
      queryClient.invalidateQueries({ queryKey: ['lifecycleManagement'] });
      onClose();
    } catch (err: any) {
      alert(err?.message ?? 'Delete failed');
    }
  }

  // ── Delete catalog item ───────────────────────────────────────

  async function handleDeleteCatalog(itemId: string) {
    try {
      await api.delete<any>(`/technology-stack/apps/${currentAppId}/catalog/${itemId}`);
      queryClient.invalidateQueries({ queryKey: ['appCatalog'] });
      setDeleteTarget(null);
    } catch (err: any) {
      alert(err?.message ?? 'Delete failed');
    }
  }

  // ── Checking ──────────────────────────────────────────────────

  async function handleChecking() {
    setCheckingLoading(true);
    setCheckingMsg('');
    try {
      const result: any = await api.post<any>(`/technology-stack/apps/${currentAppId}/checking`, {});
      setCheckingMsg(result?.message ?? 'Done');
      if (!result?.alreadyUpToDate) {
        queryClient.invalidateQueries({ queryKey: ['appCatalog'] });
      }
    } catch (err: any) {
      setCheckingMsg(err?.message ?? 'Checking failed');
    } finally {
      setCheckingLoading(false);
    }
  }

  async function handleAddMember(selected: { itcode: string }[]) {
    if (!selected.length) return;
    setAddMemberLoading(true);
    setAddMemberOpen(false);
    try {
      await api.post<any>(`/technology-stack/apps/${currentAppId}/team-members`, {
        itcodes: selected.map((s) => s.itcode),
      });
      queryClient.invalidateQueries({ queryKey: ['appTeamMembers'] });
    } catch (err: any) {
      modal.error({ title: 'Error', content: err?.message ?? 'Failed to add members', zIndex: 80 });
    } finally {
      setAddMemberLoading(false);
    }
  }

  async function handleRemoveMember(memberId: string, itcode: string) {
    modal.confirm({
      title: 'Remove Team Member',
      content: `Remove ${itcode} from this application?`,
      okText: 'Remove',
      okButtonProps: { danger: true },
      cancelText: 'Cancel',
      zIndex: 80,
      onOk: async () => {
        try {
          await api.delete<any>(`/technology-stack/apps/${currentAppId}/team-members/${memberId}`);
          queryClient.invalidateQueries({ queryKey: ['appTeamMembers'] });
        } catch (err: any) {
          modal.error({ title: 'Error', content: err?.message ?? 'Failed to remove member', zIndex: 80 });
        }
      },
    });
  }

  const gd = currentMode === 'detail' ? (detailData ?? {}) : (generalData ?? {});

  // Ownership-aware write check for the selected application.
  //
  // EA_Admin (*:*) — can write any application (bypass)
  // App_Owner     — has tech_stack_master:write, but scoped to owned apps:
  //                 check CMDB owner fields + application_member (teamData)
  // Others        — tech_stack_master:read only → canWrite = false
  const canWriteApp = useMemo(() => {
    if (isAdmin) return true;
    if (!canWrite) return false;
    if (!user) return false;

    const userId = user.id?.toLowerCase();
    if (!userId) return false;

    // Check CMDB ownership fields
    const ownerFields = [
      gd.applicationItOwner,
      gd.applicationDtOwner,
      gd.applicationOperationOwner,
    ].filter(Boolean).map((v: string) => v.toLowerCase());

    if (ownerFields.includes(userId)) return true;

    // Check application_member (teamData)
    const members = Array.isArray(teamData) ? teamData : (teamData as any)?.data ?? [];
    const memberItcodes = members.map((m: any) => (m.itcode || '').toLowerCase());
    if (memberItcodes.includes(userId)) return true;

    return false;
  }, [isAdmin, canWrite, user, gd, teamData]);

  // ── Render ────────────────────────────────────────────────────

  return (
    <>
      {contextHolder}
      <div className="fixed inset-0 z-50 bg-black/40" role="dialog" aria-modal="true" aria-label="Application Technology Stack">
        <div className="absolute right-0 top-0 h-full w-[1100px] max-w-full bg-white shadow-2xl flex flex-col">

        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b">
          <button onClick={onClose} className="flex items-center text-gray-500 hover:text-gray-700 shrink-0" aria-label="Close">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-base font-semibold text-gray-800 flex-1">Application Technology Stack</h2>
          <div className="flex items-center gap-3">
            {currentMode === 'new' && (
              <>
                {saveError && <p className="text-sm text-red-500">{saveError}</p>}
                <Button onClick={onClose}>Close</Button>
                <Button
                  type="primary"
                  onClick={handleSaveNew}
                  loading={saving}
                  disabled={!generalData}
                >
                  Save
                </Button>
              </>
            )}
            {currentMode === 'detail' && canWriteApp && (
              <Button danger onClick={handleDeleteApp} icon={<Trash2 className="w-3.5 h-3.5" />}>
                Delete
              </Button>
            )}
          </div>
        </div>

        {/* General Data */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-6 pt-5 pb-4 border-b">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">General Data</p>
            <div className="grid grid-cols-2 gap-x-12 gap-y-3">
              {/* Left column */}
              <div className="space-y-3">
                <GDRow
                  label="Application ID"
                  required={currentMode === 'new'}
                  value={
                    currentMode === 'new'
                      ? (generalData?.appId ?? '')
                      : gd.appId
                  }
                />
                <GDRow label="Application Name" value={gd.applicationName} />
                <GDRow label="Application Ownership" value={gd.applicationOwnership} />
                <GDRow label="Application Classification" value={gd.applicationClassification} />
                <GDRow label="Function (Value Chain)" value={gd.functionValueChain} />
                <GDRow label="Application IT Owner" value={gd.applicationItOwner} />
              </div>
              {/* Right column */}
              <div className="space-y-3">
                <GDRow label="Application Portfolio Management" value={gd.portfolioManagement} />
                <GDRow label="Application Solution Type" value={gd.applicationSolutionType} />
                <GDRow label="Application Status" value={gd.applicationStatus} />
                <GDRow label="Created By" value={gd.createdBy} />
                <GDRow label="Created At" value={gd.createdAt ? dayjs(gd.createdAt).format('YYYY-MM-DD HH:mm:ss') : ''} />
              </div>
            </div>
          </div>

        {/* Detail tabs */}
        {currentMode === 'detail' && (
          <div className="px-6 pt-4 pb-6">
            {/* Tab bar */}
            <div className="flex border-b mb-4">
              {(['catalog', 'team', 'log'] as ActiveTab[]).map((tab) => {
                const labels: Record<ActiveTab, string> = {
                  catalog: 'Key Technology Stack Catalog',
                  team: 'Team Members',
                  log: 'Changed Log',
                };
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-sm border-b-2 -mb-px transition-colors ${
                      activeTab === tab
                        ? 'border-primary-blue text-primary-blue font-medium'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {labels[tab]}
                  </button>
                );
              })}
            </div>

            {/* Catalog Tab */}
            {activeTab === 'catalog' && (
              <div>
                {/* Toolbar */}
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  {canWriteApp && (
                    <>
                      <Button
                        type="default"
                        icon={<Plus className="w-3.5 h-3.5" />}
                        onClick={() => setCatalogItemModal({ open: true })}
                      >
                        Add
                      </Button>
                      <Button
                        icon={<RefreshCw className={`w-3.5 h-3.5 ${checkingLoading ? 'animate-spin' : ''}`} />}
                        loading={checkingLoading}
                        onClick={handleChecking}
                      >
                        Checking
                      </Button>
                    </>
                  )}
                  {/* Filters */}
                  <Select
                    placeholder="Category"
                    value={catalogFilters.category || undefined}
                    onChange={(v) =>
                      setCatalogFilters((f) => ({
                        ...f,
                        category: v ?? '',
                        subCategory: '',
                      }))
                    }
                    allowClear
                    style={{ width: 150 }}
                    options={categoryOptions}
                  />
                  <Select
                    placeholder="Sub Category"
                    value={catalogFilters.subCategory || undefined}
                    onChange={(v) => setCatalogFilters((f) => ({ ...f, subCategory: v ?? '' }))}
                    allowClear
                    disabled={!catalogFilters.category}
                    style={{ width: 150 }}
                    options={subCategoryOptions}
                  />
                  <Input
                    placeholder="Technology Component"
                    value={catalogFilters.component}
                    onChange={(e) => setCatalogFilters((f) => ({ ...f, component: e.target.value }))}
                    allowClear
                    style={{ width: 180 }}
                  />
                  <Select
                    placeholder="Use Status"
                    value={catalogFilters.useStatus || undefined}
                    onChange={(v) => setCatalogFilters((f) => ({ ...f, useStatus: v ?? '' }))}
                    allowClear
                    style={{ width: 130 }}
                    options={['Used', 'Deprecated'].map(o => ({ label: o, value: o }))}
                  />
                </div>

                {checkingMsg && (
                  <div className="mb-3 px-3 py-2 text-sm bg-blue-50 border border-blue-200 rounded text-blue-700">
                    {checkingMsg}
                  </div>
                )}

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-gray-50 text-gray-600">
                        {['Stack ID', 'Security Risk Level', 'EOL Date', 'EOL Interval', 'Maint. Risk', 'Category', 'Sub Category', 'Component', 'Package', 'EA Advice', 'Security Advice', 'Major', 'Minor', 'Patch', 'Operation'].map((h) => (
                          <th key={h} className="px-2 py-2 text-left font-medium border-b border-gray-200 whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {catalogLoading && (
                        <tr><td colSpan={15} className="text-center py-8 text-gray-400">Loading…</td></tr>
                      )}
                      {!catalogLoading && (!catalogData?.data || catalogData.data.length === 0) && (
                        <tr><td colSpan={15} className="text-center py-8 text-gray-400">No Data</td></tr>
                      )}
                      {(catalogData?.data ?? []).map((row: any) => (
                        <tr key={row.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="px-2 py-2 font-mono">{row.stackId}</td>
                          <td className="px-2 py-2"><RiskLevelBadge level={row.securityRiskLevel} /></td>
                          <td className="px-2 py-2">{row.eolDate ? String(row.eolDate).slice(0, 10) : '—'}</td>
                          <td className="px-2 py-2">{row.eolIntervalTime ?? '—'}</td>
                          <td className="px-2 py-2"><RiskLevelBadge level={row.maintainabilityRiskLevel} /></td>
                          <td className="px-2 py-2">{row.category}</td>
                          <td className="px-2 py-2">{row.subCategory}</td>
                          <td className="px-2 py-2">{row.component}</td>
                          <td className="px-2 py-2">{row.componentPackage}</td>
                          <td className="px-2 py-2">{row.eaAdvice ?? '—'}</td>
                          <td className="px-2 py-2">{row.securityAdvice ?? '—'}</td>
                          <td className="px-2 py-2">{row.majorVersion}</td>
                          <td className="px-2 py-2">{row.minorVersion}</td>
                          <td className="px-2 py-2">{row.patchVersion ?? '—'}</td>
                          <td className="px-2 py-2">
                            {canWriteApp && (
                              <div className="flex gap-2">
                                <Button
                                  type="text"
                                  size="small"
                                  icon={<Pencil className="w-3.5 h-3.5" />}
                                  onClick={() => setCatalogItemModal({ open: true, item: row })}
                                />
                                <Button
                                  type="text"
                                  size="small"
                                  danger
                                  icon={<Trash2 className="w-3.5 h-3.5" />}
                                  onClick={() => setDeleteTarget({ id: row.id, label: row.stackId })}
                                />
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination info */}
                {catalogData && (
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-gray-500">Total {catalogData.total ?? 0} Items</span>
                    <Pagination
                      current={catalogPage}
                      total={catalogData.total ?? 0}
                      pageSize={10}
                      onChange={(p) => setCatalogPage(p)}
                      showSizeChanger={false}
                      size="small"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Team Members Tab */}
            {activeTab === 'team' && (
              <div className="space-y-3">
                {/* Toolbar */}
                <div className="flex items-center gap-2">
                  {canWriteApp && (
                    <Button
                      type="dashed"
                      icon={<Plus size={14} />}
                      loading={addMemberLoading}
                      onClick={() => setAddMemberOpen(true)}
                    >
                      Add Team Members
                    </Button>
                  )}
                  <div className="relative group ml-1">
                    <span className="cursor-pointer text-gray-400 hover:text-gray-600">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                    </span>
                    <div className="absolute left-6 top-0 z-10 hidden group-hover:block w-80 bg-white border border-gray-200 rounded shadow-lg p-3 text-xs text-gray-600">
                      <p className="font-medium mb-1">By Application add/remove &quot;Team Members&quot;</p>
                      <p>                      1) AxisArch Admin、BigEA、CMDB Application IT Owner and Creator can add/remove members ;</p>
                      <p className="mt-1">2) Team members can update technology stack about the application ;</p>
                    </div>
                  </div>
                </div>
                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-50 text-gray-600">
                        {['IT Code', 'Name', 'Worker Type', 'Manager IT Code', 'Added At', ...(canWriteApp ? ['Action'] : [])].map((h) => (
                          <th key={h} className="px-3 py-2 text-left font-medium border-b">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(!teamData || (Array.isArray(teamData) ? teamData : teamData?.data ?? []).length === 0) && (
                        <tr><td colSpan={canWriteApp ? 6 : 5} className="text-center py-8 text-gray-400">No Data</td></tr>
                      )}
                      {(Array.isArray(teamData) ? teamData : teamData?.data ?? []).map((m: any, i: number) => (
                        <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="px-3 py-2">{m.itcode}</td>
                          <td className="px-3 py-2">{m.name}</td>
                          <td className="px-3 py-2">{m.workerType}</td>
                          <td className="px-3 py-2">{m.managerItcode}</td>
                          <td className="px-3 py-2">{m.createAt ? dayjs(m.createAt).format('YYYY-MM-DD HH:mm:ss') : ''}</td>
                          {canWriteApp && (
                            <td className="px-3 py-2">
                              <Button
                                size="small"
                                danger
                                icon={<Trash2 size={12} />}
                                onClick={() => handleRemoveMember(m.id, m.itcode)}
                              />
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Changed Log Tab */}
            {activeTab === 'log' && (
              <div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-50 text-gray-600">
                        {['Stack ID', 'Field', 'Old Value', 'New Value', 'Changed By', 'Changed At'].map((h) => (
                          <th key={h} className="px-3 py-2 text-left font-medium border-b">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(!logData || (logData?.items ?? []).length === 0) && (
                        <tr><td colSpan={6} className="text-center py-8 text-gray-400">No Data</td></tr>
                      )}
                      {(logData?.items ?? []).map((l: any, i: number) => (
                        <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 text-xs">
                          <td className="px-3 py-2 font-mono">{l.stackId}</td>
                          <td className="px-3 py-2">{l.field}</td>
                          <td className="px-3 py-2 text-gray-500">{l.oldValue ?? '—'}</td>
                          <td className="px-3 py-2">{l.newValue ?? '—'}</td>
                          <td className="px-3 py-2">{l.createBy}</td>
                          <td className="px-3 py-2">{l.createAt ? dayjs(l.createAt).format('YYYY-MM-DD HH:mm:ss') : ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {logData && (
                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-gray-500">Total {logData.total ?? 0} Items</span>
                    <Pagination
                      current={logPage}
                      total={logData.total ?? 0}
                      pageSize={20}
                      onChange={(p) => setLogPage(p)}
                      showSizeChanger={false}
                      size="small"
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        </div>{/* end flex-1 scroll wrapper */}
      </div>
      </div>

      {/* CatalogItemModal */}
      {catalogItemModal.open && (
        <CatalogItemModal
          appId={currentAppId}
          item={catalogItemModal.item}
          onClose={() => setCatalogItemModal({ open: false })}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['appCatalog'] });
            queryClient.invalidateQueries({ queryKey: ['appOperateLog'] });
          }}
        />
      )}

      {/* Resource Pool Picker */}
      {addMemberOpen && (
        <ResourcePoolPickerModal
          onClose={() => setAddMemberOpen(false)}
          onConfirm={(selected) => handleAddMember(selected)}
        />
      )}

      {/* CmdbPickerModal removed — picker is now opened from the list page */}

      {/* Delete confirm */}
      {deleteTarget && (
        <Modal
          open={!!deleteTarget}
          title="Confirm Delete"
          onOk={() => handleDeleteCatalog(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
          okText="Confirm"
          okButtonProps={{ danger: true }}
          cancelText="Cancel"
          zIndex={80}
        >
          <p className="text-sm text-gray-700">
            Confirm delete catalog item <strong>{deleteTarget.label}</strong>?
          </p>
        </Modal>
      )}
    </>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function GDRow({ label, required, value }: { label: string; required?: boolean; value?: any }) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-500 w-52 shrink-0 text-right">
        {required && <span className="text-red-500 mr-0.5">*</span>}
        {label}
      </label>
      {typeof value === 'string' || typeof value === 'number' || value === undefined || value === null ? (
        <div className="flex-1 px-2 py-1 text-sm bg-gray-100 border border-gray-200 rounded min-h-[30px]">
          {value ?? ''}
        </div>
      ) : (
        <div className="flex-1">{value}</div>
      )}
    </div>
  );
}

