'use client';

import { useRef, useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { API_BASE, api, authFetch } from '@/shared/lib/api';
import { authHeaders } from '@/shared/lib/auth-token';
import { useLocale, useT } from '@/shared/lib/locale';
import { Button, Card, Radio, Spin, Tooltip, message, Select, Modal, Input, Popconfirm, App } from 'antd';
import { AppArchReportDrawer } from '@/features/review/components/ea-review/request-detail/AppArchReportDrawer';
import { TechArchReportDrawer } from '@/features/review/components/ea-review/request-detail/TechArchReportDrawer';
import { ImageViewerModal } from '@/features/review/components/ea-review/request-detail/modals/ImageViewerModal';
import {
  PlusOutlined,
  DeleteOutlined,
  LoadingOutlined,
  SyncOutlined,
  CloudUploadOutlined,
  FileOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

/* ── Types ── */
export interface UploadedAttachment {
  id: string;          // attachmentUuid
  fileName: string;
  originalName?: string;   // user's original uploaded file name
  attachmentName: string;  // relative path on server
  appArchType?: string;
  aiScore?: number | null;
  aiResult?: Record<string, unknown>;
  aiCheckId?: string;      // UUID of eam_arch_ai_check record
  thumbnailUrl?: string;   // generated client-side for preview
}

interface DiagramUploadCardProps {
  /** The EA request id to associate uploads with */
  requestId: string;
  /** Business type: App_Arch, Tech_Arch, or Proj_Intro */
  bizType: 'App_Arch' | 'Tech_Arch' | 'Proj_Intro';
  /** Whether per-card App Arch Type radio is shown (only for App_Arch) */
  showArchTypeRadio?: boolean;
  /** Current list of attachments for this section */
  attachments: UploadedAttachment[];
  /** Callback when attachments list changes */
  onChange: (attachments: UploadedAttachment[]) => void;
  /** Accept mime types (default image/*) */
  accept?: string;
  /** Disable AI scoring (e.g. Proj_Intro) */
  disableAiCheck?: boolean;
  /** Allow selecting multiple files at once */
  multiple?: boolean;
  /** Read-only mode: disable upload and delete */
  readOnly?: boolean;
}

/* ── Authenticated image: fetches with Bearer token, renders as blob ── */
function AuthImage({ src, alt, className, style, onClick }: { src: string; alt: string; className?: string; style?: Record<string, string | number>; onClick?: (blobUrl: string) => void }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch(src, { headers: { ...authHeaders() } })
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (blob && !cancelled) setBlobUrl(URL.createObjectURL(blob));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);
  if (!blobUrl) return <div className={`${className} bg-gray-100 animate-pulse`} style={style} />;
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={blobUrl} alt={alt} className={`${className ?? ''} ${onClick ? 'cursor-zoom-in' : ''}`} style={style} onClick={() => blobUrl && onClick?.(blobUrl)} />;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function DiagramUploadCard({
  requestId,
  bizType,
  showArchTypeRadio = false,
  attachments,
  onChange,
  accept = 'image/*',
  disableAiCheck = false,
  multiple = false,
  readOnly = false,
}: DiagramUploadCardProps) {
  const [messageApi, contextHolder] = message.useMessage();
  const { modal } = App.useApp();
  const { locale } = useLocale();
  const t = useT();
  const queryClient = useQueryClient();

  /* ── New card state (pre-upload): type already selected on the empty card ── */
  const [newCardArchType, setNewCardArchType] = useState<string>('E2E_Solution');
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ── AI Detail Drawer state ── */
  const [aiDetail, setAiDetail] = useState<any>(null);
  const [aiDrawerTab, setAiDrawerTab] = useState('score');
  const [aiIssueFilter, setAiIssueFilter] = useState<string[]>([]);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerSrc, setViewerSrc] = useState<string | null>(null);

  /* ── App tab state ── */
  const [appPage, setAppPage] = useState(1);
  const [appPageSize, setAppPageSize] = useState(10);
  const [appSelectedKeys, setAppSelectedKeys] = useState<React.Key[]>([]);
  const [addAppOpen, setAddAppOpen] = useState(false);
  const [editAppRecord, setEditAppRecord] = useState<any>(null);
  const [addAppForm, setAddAppForm] = useState({ applicationId: '', applicationName: '', applicationClassification: '', valueChain: '', solutionOwner: '', changeStatus: '', eaComments: '' });
  const [addAppErrors, setAddAppErrors] = useState<{ applicationId?: string; changeStatus?: string }>({});
  const [appSearchKeyword, setAppSearchKeyword] = useState('');

  /* ── Interface tab state ── */
  const [intfPage, setIntfPage] = useState(1);
  const [intfPageSize, setIntfPageSize] = useState(10);
  const [intfSelectedKeys, setIntfSelectedKeys] = useState<React.Key[]>([]);
  const [addIntfOpen, setAddIntfOpen] = useState(false);
  const [editIntfRecord, setEditIntfRecord] = useState<any>(null);
  const [addIntfForm, setAddIntfForm] = useState({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' });
  const [addIntfErrors, setAddIntfErrors] = useState<{ sourceAppId?: string; targetAppId?: string; changeStatus?: string }>({});
  const [intfSourceSearchKeyword, setIntfSourceSearchKeyword] = useState('');
  const [intfTargetSearchKeyword, setIntfTargetSearchKeyword] = useState('');

  /* Keep a ref to the latest attachments to avoid stale closures in multi-file uploads */
  const attachmentsRef = useRef(attachments);
  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  /* ── Upload mutation ── */
  const uploadMutation = useMutation({
    mutationFn: async ({ file, archType }: { file: File; archType?: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('requestId', requestId);
      formData.append('bizType', bizType);
      if (bizType === 'App_Arch' && archType) {
        formData.append('appArchType', archType);
      }
      // Generate a display file name with a timestamp.
      const now = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      const dateStr = `_${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
      const dotIdx = file.name.lastIndexOf('.');
      const base = dotIdx > 0 ? file.name.slice(0, dotIdx) : file.name;
      const ext = dotIdx > 0 ? file.name.slice(dotIdx) : '';
      const fileNameWithDate = base + dateStr + ext;
      formData.append('originalName', fileNameWithDate);
      const resp = await authFetch(`${API_BASE}/ea-requests/attachments/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
      }
      return { data: await resp.json(), archType, file };
    },
    onSuccess: ({ data, archType, file }) => {
      const thumbUrl = file.type.startsWith('image/')
        ? URL.createObjectURL(file)
        : undefined;
      const newAttachment: UploadedAttachment = {
        id: data.attachmentUuid,
        fileName: data.originalName || file.name,
        originalName: data.originalName || file.name,
        attachmentName: data.attachmentName,
        appArchType: bizType === 'App_Arch' ? archType : undefined,
        aiScore: null,
        thumbnailUrl: thumbUrl,
      };
      const updated = [...attachmentsRef.current, newAttachment];
      onChange(updated);
      messageApi.success('Uploaded successfully');
      // Auto-trigger AI check (unless disabled)
      if (!disableAiCheck) {
        triggerAiCheck(newAttachment, updated);
      }
    },
    onError: (err: Error) => {
      messageApi.error(err.message || 'Upload failed');
    },
  });

  /* ── Delete mutation ── */
  const deleteMutation = useMutation({
    mutationFn: (attachmentId: string) =>
      api.delete(`/ea-requests/attachments/${attachmentId}`),
    onSuccess: (_, attachmentId) => {
      onChange(attachments.filter((a) => a.id !== attachmentId));
      messageApi.success('Deleted');
    },
    onError: () => messageApi.error('Failed to delete'),
  });

  /* ── AI Check mutation ── */
  const [checkingId, setCheckingId] = useState<string | null>(null);
  const aiCheckMutation = useMutation({
    mutationFn: (att: UploadedAttachment) =>
      api.post<Record<string, unknown>>('/ea-requests/attachments/ai-check', {
        requestId,
        bizType,
        language: locale,
        attachmentName: att.attachmentName,
        attachmentUuid: att.id,
      }),
    onError: (err: Error & { detail?: string }) => {
      setCheckingId(null);
      messageApi.error(err?.message || 'AI check failed');
    },
  });

  const triggerAiCheck = (att: UploadedAttachment, currentList: UploadedAttachment[]) => {
    setCheckingId(att.id);
    aiCheckMutation.mutate(att, {
      onSuccess: (data) => {
        const score = typeof data?.score === 'number' ? data.score : null;
        const aiCheckId = typeof data?.aiCheckId === 'string' ? data.aiCheckId : undefined;
        onChange(
          currentList.map((a) =>
            a.id === att.id
              ? { ...a, aiScore: score, aiResult: data?.result as Record<string, unknown> | undefined, aiCheckId }
              : a
          )
        );
        setCheckingId(null);
      },
    });
  };

  /* ── CMDB search for Add App modal ── */
  const { data: cmdbApps, isFetching: cmdbFetching } = useQuery({
    queryKey: ['cmdbAppSearch', appSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: appSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: addAppOpen,
  });
  const { data: intfSourceApps, isFetching: intfSourceFetching } = useQuery({
    queryKey: ['cmdbAppSearch', 'intfSource', intfSourceSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: intfSourceSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: addIntfOpen,
  });
  const { data: intfTargetApps, isFetching: intfTargetFetching } = useQuery({
    queryKey: ['cmdbAppSearch', 'intfTarget', intfTargetSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: intfTargetSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: addIntfOpen,
  });

  /* ── Arch check apps / interactions queries ── */
  const { data: archCheckApps, isFetching: archCheckAppsFetching } = useQuery({
    queryKey: ['archCheckApps', aiDetail?._aiCheckId],
    queryFn: () => api.get<any[]>('/arch-check-apps', { aiCheckId: aiDetail!._aiCheckId }),
    enabled: !!aiDetail?._aiCheckId && aiDrawerTab === 'applications',
  });
  const { data: archCheckInteractions, isFetching: archCheckInteractionsFetching } = useQuery({
    queryKey: ['archCheckInteractions', aiDetail?._aiCheckId],
    queryFn: () => api.get<any[]>('/arch-check-interactions', { aiCheckId: aiDetail!._aiCheckId }),
    enabled: !!aiDetail?._aiCheckId && aiDrawerTab === 'interfaces',
  });

  /* ── App mutations ── */
  const confirmArchCheckApps = useMutation({
    mutationFn: (checkAppUuids: React.Key[]) => api.post<any>('/arch-check-apps/confirm', { checkAppUuids }),
    onSuccess: () => { messageApi.success('Applications confirmed'); setAppSelectedKeys([]); queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to confirm applications'),
  });
  const addArchCheckApp = useMutation({
    mutationFn: (p: any) => api.post<any>('/arch-check-apps', p),
    onSuccess: () => { setAddAppOpen(false); messageApi.success('Application added'); queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to add application'),
  });
  const updateArchCheckApp = useMutation({
    mutationFn: (p: any) => api.put<any>(`/arch-check-apps/${p.checkAppUuid}`, p),
    onSuccess: () => { setAddAppOpen(false); setEditAppRecord(null); messageApi.success('Application updated'); queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to update application'),
  });
  const deleteArchCheckApp = useMutation({
    mutationFn: (uuid: string) => api.delete<any>(`/arch-check-apps/${uuid}`),
    onSuccess: () => { messageApi.success('Application deleted'); queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to delete application'),
  });

  /* ── Interface mutations ── */
  const confirmArchCheckInteractions = useMutation({
    mutationFn: (uuids: React.Key[]) => api.post<any>('/arch-check-interactions/confirm', { interactionUuids: uuids }),
    onSuccess: () => { messageApi.success('Interactions confirmed'); setIntfSelectedKeys([]); queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to confirm interactions'),
  });
  const addArchCheckInteraction = useMutation({
    mutationFn: (p: any) => api.post<any>('/arch-check-interactions', p),
    onSuccess: () => { setAddIntfOpen(false); setEditIntfRecord(null); messageApi.success('Interaction added'); queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to add interaction'),
  });
  const updateArchCheckInteraction = useMutation({
    mutationFn: (p: any) => api.put<any>(`/arch-check-interactions/${p.interactionUuid}`, p),
    onSuccess: () => { setAddIntfOpen(false); setEditIntfRecord(null); messageApi.success('Interaction updated'); queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to update interaction'),
  });
  const deleteArchCheckInteraction = useMutation({
    mutationFn: (uuid: string) => api.delete<any>(`/arch-check-interactions/${uuid}`),
    onSuccess: () => { messageApi.success('Interaction deleted'); queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] }); },
    onError: () => messageApi.error('Failed to delete interaction'),
  });


  const uploadFiles = async (files: File[]) => {
    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        messageApi.error(`${file.name} exceeds 10MB limit`);
        continue;
      }
      try {
        await uploadMutation.mutateAsync({
          file,
          archType: bizType === 'App_Arch' ? newCardArchType : undefined,
        });
      } catch {
        // error already handled by onError
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    e.target.value = '';
    await uploadFiles(files);
  };

  /* ── Drag & drop ── */
  const [isDragging, setIsDragging] = useState(false);
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (!files.length) return;
    await uploadFiles(files);
  };

  const closeAiDrawer = () => {
    setAiDetail(null);
    setAiIssueFilter([]);
    setAiDrawerTab('score');
    setAppPage(1);
    setAppSelectedKeys([]);
    setIntfPage(1);
    setIntfSelectedKeys([]);
  };

  const openAddApp = () => {
    setEditAppRecord(null);
    setAddAppForm({ applicationId: '', applicationName: '', applicationClassification: '', valueChain: '', solutionOwner: '', changeStatus: '', eaComments: '' });
    setAddAppErrors({});
    setAppSearchKeyword('');
    setAddAppOpen(true);
  };

  const openEditApp = (record: any) => {
    setEditAppRecord(record);
    setAddAppForm({
      applicationId: record.appId ?? '',
      applicationName: record.appName ?? '',
      applicationClassification: record.appClassification ?? '',
      valueChain: record.bizFunction ?? '',
      solutionOwner: record.appSolutionOwnerName ?? '',
      changeStatus: record.checkAppStatus ?? '',
      eaComments: record.remark ?? '',
    });
    setAddAppErrors({});
    setAppSearchKeyword('');
    setAddAppOpen(true);
  };

  const openAddInterface = () => {
    setEditIntfRecord(null);
    setAddIntfForm({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' });
    setAddIntfErrors({});
    setIntfSourceSearchKeyword('');
    setIntfTargetSearchKeyword('');
    setAddIntfOpen(true);
  };

  const openEditInterface = (record: any) => {
    setEditIntfRecord(record);
    setAddIntfForm({
      sourceAppId: record.sourceAppId ?? '',
      applicationName: record.sourceAppName ?? '',
      targetAppId: record.targetAppId ?? '',
      targetAppName: record.targetAppName ?? '',
      businessObject: record.businessObject ?? '',
      integrationType: record.interactionType ?? '',
      direction: record.direction ?? '',
      changeStatus: record.interfaceStatus ?? '',
    });
    setAddIntfErrors({});
    setIntfSourceSearchKeyword('');
    setIntfTargetSearchKeyword('');
    setAddIntfOpen(true);
  };

  /* ── Simple file-list layout (Proj_Intro / disableAiCheck) ── */
  if (disableAiCheck) {
    return (
      <>
        {contextHolder}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className="hidden"
          onChange={handleFileSelect}
        />

        {/* Drag-and-drop zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-400 bg-blue-50'
              : 'border-[#40a9ff] bg-white hover:bg-gray-50'
          }`}
          onClick={() => !uploadMutation.isPending && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {uploadMutation.isPending ? (
            <Spin indicator={<LoadingOutlined style={{ fontSize: 32 }} />} />
          ) : (
            <>
              <CloudUploadOutlined style={{ fontSize: 32, color: '#40a9ff' }} />
              <div className="mt-2 text-gray-500">
                Drag a file here, or{' '}
                <span className="text-blue-500 cursor-pointer">click to upload</span>
              </div>
              <div className="mt-1 text-xs text-gray-400">Supports images, PDF, PPT, Word, Excel documents</div>
            </>
          )}
        </div>

        {/* File list */}
        {attachments.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {attachments.map((att) => (
              <div key={att.id} className="flex items-center gap-2 text-sm text-gray-600">
                <FileOutlined className="text-gray-400" />
                <span className="flex-1 truncate" title={att.fileName}>
                  {att.fileName}
                </span>
                <CheckCircleOutlined className="text-green-500" style={{ fontSize: 14 }} />
                {!readOnly && (
                  <Tooltip title="Delete">
                    <DeleteOutlined
                      className="text-gray-400 hover:text-red-500 cursor-pointer"
                      style={{ fontSize: 14 }}
                      onClick={() => deleteMutation.mutate(att.id)}
                    />
                  </Tooltip>
                )}
              </div>
            ))}
          </div>
        )}
      </>
    );
  }

  /* ── Card-grid layout (App_Arch / Tech_Arch) ── */
  return (
    <>
      {contextHolder}
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={handleFileSelect}
      />

      <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
        {/* ── Empty "new upload" card - hide in read-only mode ── */}
        {!readOnly && (
          <Card
            size="small"
            className="bg-[#fafafa]"
            styles={{ body: { padding: '12px 16px' } }}
          >
          {/* App Arch Type radio (pre-select before upload) */}
          {showArchTypeRadio && (
            <div className="mb-3 flex items-center gap-2 text-xs">
              <span className="text-red-500">*</span>
              <span className="whitespace-nowrap">App Arch Type</span>
              <Radio.Group
                size="small"
                value={newCardArchType}
                onChange={(e) => setNewCardArchType(e.target.value)}
                disabled={readOnly}
              >
                <Radio value="New_App">New App</Radio>
                <Radio value="E2E_Solution">E2E Solution</Radio>
              </Radio.Group>
            </div>
          )}

          <div className="flex gap-3">
            {/* Upload placeholder - hide in read-only mode */}
            {!readOnly && (
              <div
                className="w-[100px] h-[72px] border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center text-gray-400 cursor-pointer hover:border-blue-400 hover:text-blue-400 transition-colors shrink-0"
                onClick={() => !uploadMutation.isPending && fileInputRef.current?.click()}
              >
                {uploadMutation.isPending ? (
                  <Spin indicator={<LoadingOutlined style={{ fontSize: 20 }} />} />
                ) : (
                  <PlusOutlined style={{ fontSize: 20 }} />
                )}
              </div>
            )}

            <div className="flex flex-col justify-center text-sm text-gray-400">
              <div>AI Evaluation Score</div>
              <div className="text-blue-500 mt-1 text-lg font-medium">-</div>
            </div>
          </div>
        </Card>
        )}

        {/* ── Uploaded attachment cards ── */}
        {attachments.map((att) => (
          <Card
            key={att.id}
            size="small"
            className="bg-[#fafafa]"
            styles={{ body: { padding: '12px 16px' } }}
          >
            {showArchTypeRadio && (
              <div className="mb-3 flex items-center gap-2 text-xs">
                <span className="text-red-500">*</span>
                <span className="whitespace-nowrap">App Arch Type</span>
                <Radio.Group
                  size="small"
                  value={att.appArchType || 'E2E_Solution'}
                  disabled
                >
                  <Radio value="New_App">New App</Radio>
                  <Radio value="E2E_Solution">E2E Solution</Radio>
                </Radio.Group>
              </div>
            )}

            <div className="flex gap-3">
              <div className="border border-gray-200 rounded overflow-hidden bg-gray-50 shrink-0" style={{ width: 100, height: 72 }}>
                {att.thumbnailUrl ? (
                  <img
                    src={att.thumbnailUrl}
                    alt={att.fileName}
                    className="block cursor-zoom-in bg-white"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    onClick={() => {
                      setViewerSrc(att.thumbnailUrl ?? null);
                      setViewerOpen(true);
                    }}
                  />
                ) : (
                  <AuthImage
                    src={`${API_BASE}/ea-requests/attachments/${att.id}/file`}
                    alt={att.fileName}
                    className="block bg-white"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    onClick={(blobUrl) => {
                      setViewerSrc(blobUrl);
                      setViewerOpen(true);
                    }}
                  />
                )}
              </div>

              <div className="flex-1 min-w-0 flex flex-col justify-between">
                <div className="flex items-start gap-1">
                  <div className="text-xs text-gray-600 truncate flex-1" title={att.fileName}>
                    {att.fileName}
                  </div>
                  {!readOnly && (
                    <Tooltip title="Delete">
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        loading={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(att.id)}
                        className="shrink-0"
                      />
                    </Tooltip>
                  )}
                </div>

                <div className="text-xs text-gray-400">AI Evaluation Score</div>
                <div className="flex items-center gap-1">
                  {checkingId === att.id ? (
                    <span className="flex items-center gap-1 text-blue-500 text-sm">
                      <Spin indicator={<LoadingOutlined style={{ fontSize: 14 }} />} size="small" />
                    </span>
                  ) : att.aiScore != null ? (
                    <span className="flex items-center gap-1">
                      <Tooltip title="View AI evaluation detail">
                        <span
                          className={`text-lg font-semibold cursor-pointer hover:opacity-70 ${
                            att.aiScore >= 7 ? 'text-green-600' : 'text-orange-500'
                          }`}
                          onClick={() => {
                            setAiIssueFilter([]);
                            setAiDrawerTab('score');
                            setAppPage(1);
                            setAppSelectedKeys([]);
                            setIntfPage(1);
                            setIntfSelectedKeys([]);
                            setAiDetail({ ...(att.aiResult ?? {}), _attachmentId: att.id, _fileName: att.fileName, _archType: att.appArchType, _bizType: bizType, _aiCheckId: att.aiCheckId });
                          }}
                        >
                          {att.aiScore}
                        </span>
                      </Tooltip>
                      <Tooltip title="Re-run AI check">
                        <SyncOutlined
                          className="text-gray-400 hover:text-blue-500 cursor-pointer"
                          style={{ fontSize: 12 }}
                          onClick={() => triggerAiCheck(att, attachments)}
                        />
                      </Tooltip>
                    </span>
                  ) : (
                    <Tooltip title="Re-run AI check">
                      <SyncOutlined
                        className="text-gray-400 hover:text-blue-500 cursor-pointer"
                        style={{ fontSize: 14 }}
                        onClick={() => triggerAiCheck(att, attachments)}
                      />
                    </Tooltip>
                  )}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* ── AI Evaluation Detail Drawer ── */}
      {aiDetail?._bizType === 'Tech_Arch' ? (
        <TechArchReportDrawer
          open={!!aiDetail}
          aiDetail={aiDetail}
          t={t}
          aiIssueFilter={aiIssueFilter}
          setAiIssueFilter={setAiIssueFilter}
          onClose={closeAiDrawer}
        />
      ) : (
        <AppArchReportDrawer
          open={!!aiDetail}
          aiDetail={aiDetail}
          t={t}
          aiDrawerTab={aiDrawerTab}
          setAiDrawerTab={(tab) => { setAiDrawerTab(tab); setAppSelectedKeys([]); setIntfSelectedKeys([]); }}
          aiIssueFilter={aiIssueFilter}
          setAiIssueFilter={setAiIssueFilter}
          setViewerSrc={setViewerSrc}
          setViewerOpen={setViewerOpen}
          onClose={closeAiDrawer}
          archCheckApps={archCheckApps}
          archCheckAppsFetching={archCheckAppsFetching}
          archCheckInteractions={archCheckInteractions}
          archCheckInteractionsFetching={archCheckInteractionsFetching}
          appPage={appPage}
          appPageSize={appPageSize}
          setAppPage={setAppPage}
          setAppPageSize={setAppPageSize}
          appSelectedKeys={appSelectedKeys}
          setAppSelectedKeys={setAppSelectedKeys}
          confirmArchCheckApps={confirmArchCheckApps}
          deleteArchCheckApp={deleteArchCheckApp}
          onOpenAddApp={openAddApp}
          onOpenEditApp={openEditApp}
          intfPage={intfPage}
          intfPageSize={intfPageSize}
          setIntfPage={setIntfPage}
          setIntfPageSize={setIntfPageSize}
          intfSelectedKeys={intfSelectedKeys}
          setIntfSelectedKeys={setIntfSelectedKeys}
          confirmArchCheckInteractions={confirmArchCheckInteractions}
          deleteArchCheckInteraction={deleteArchCheckInteraction}
          onOpenAddInterface={openAddInterface}
          onOpenEditInterface={openEditInterface}
        />
      )}

      <ImageViewerModal
        open={viewerOpen}
        viewerSrc={viewerSrc}
        onClose={() => setViewerOpen(false)}
      />

      {/* ── Add / Edit Application Modal ── */}
      <Modal open={addAppOpen} onCancel={() => { setAddAppOpen(false); setEditAppRecord(null); setAppSearchKeyword(''); }} footer={null} width={760} closable title={editAppRecord ? t('Edit Application') : t('Add Application')} styles={{ body: { padding: '24px 32px 24px' } }}>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5">
          <div className="space-y-4">
            <div>
              <div className="flex items-baseline gap-1 mb-1"><span className="text-red-500 text-sm">*</span><label className="text-sm text-gray-500">{t('Application ID')}</label></div>
              <Select showSearch filterOption={false} style={{ width: '100%' }} placeholder={t('Search by App ID or Name')} value={addAppForm.applicationId || undefined} status={addAppErrors.applicationId ? 'error' : undefined} loading={cmdbFetching} onSearch={(val) => setAppSearchKeyword(val)}
                onChange={(val) => { const hit = (cmdbApps?.data ?? []).find((r: any) => r.appId === val); setAddAppForm(f => ({ ...f, applicationId: val, applicationName: hit?.name ?? hit?.appFullName ?? '', applicationClassification: hit?.appClassification ?? '', valueChain: hit?.serviceArea ?? '', solutionOwner: hit?.ownedBy ?? '' })); setAddAppErrors(e => ({ ...e, applicationId: undefined })); }}
                options={[ ...(addAppForm.applicationId && !(cmdbApps?.data ?? []).find((r: any) => r.appId === addAppForm.applicationId) ? [{ value: addAppForm.applicationId, label: `${addAppForm.applicationId} - ${addAppForm.applicationName || ''}` }] : []), ...(cmdbApps?.data ?? []).map((r: any) => ({ value: r.appId, label: `${r.appId} - ${r.name || r.appFullName || ''}` })) ]}
                notFoundContent={cmdbFetching ? t('Loading...') : t('No results')} />
              {addAppErrors.applicationId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
            </div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Application Name')}</label><Input value={addAppForm.applicationName} onChange={(e) => setAddAppForm(f => ({ ...f, applicationName: e.target.value }))} placeholder={t('Application Name')} /></div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Application Classification')}</label><Input value={addAppForm.applicationClassification} readOnly className="bg-gray-100" /></div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Value Chain')}</label><Input value={addAppForm.valueChain} readOnly className="bg-gray-100" /></div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Solution Owner')}</label><Input value={addAppForm.solutionOwner} readOnly className="bg-gray-100" /></div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex items-baseline gap-1 mb-1"><span className="text-red-500 text-sm">*</span><label className="text-sm text-gray-500">{t('Check App Status')}</label></div>
              <Select style={{ width: '100%' }} value={addAppForm.changeStatus || undefined} status={addAppErrors.changeStatus ? 'error' : undefined} onChange={(val) => setAddAppForm(f => ({ ...f, changeStatus: val }))} options={[{ value: 'New', label: 'New' }, { value: 'Keep', label: 'Keep' }, { value: 'Change', label: 'Change' }, { value: 'Sunset', label: 'Sunset' }, { value: '3rd Party', label: '3rd Party' }]} />
              {addAppErrors.changeStatus && <div className="text-red-500 text-xs mt-0.5">Required</div>}
            </div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Remark')}</label><Input.TextArea rows={4} value={addAppForm.eaComments} onChange={(e) => setAddAppForm(f => ({ ...f, eaComments: e.target.value }))} /></div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button onClick={() => { setAddAppOpen(false); setEditAppRecord(null); }}>{t('Cancel')}</Button>
          <Button type="primary" loading={editAppRecord ? updateArchCheckApp.isPending : addArchCheckApp.isPending}
            onClick={() => {
              const errors: { applicationId?: string; changeStatus?: string } = {};
              if (!addAppForm.applicationId) errors.applicationId = "Required";
              if (!addAppForm.changeStatus) errors.changeStatus = "Required";
              if (Object.keys(errors).length > 0) { setAddAppErrors(errors); return; }
              if (editAppRecord) {
                updateArchCheckApp.mutate({ checkAppUuid: editAppRecord.checkAppUuid, appId: addAppForm.applicationId, appName: addAppForm.applicationName, idIsStandard: false, checkAppStatus: addAppForm.changeStatus, remark: addAppForm.eaComments || undefined });
              } else {
                addArchCheckApp.mutate({ aiCheckId: aiDetail?._aiCheckId, appId: addAppForm.applicationId, appName: addAppForm.applicationName, idIsStandard: false, checkAppStatus: addAppForm.changeStatus, remark: addAppForm.eaComments || undefined });
              }
            }}>{t('Save')}</Button>
        </div>
      </Modal>

      {/* ── Add / Edit Interface Modal ── */}
      <Modal open={addIntfOpen} onCancel={() => { setAddIntfOpen(false); setEditIntfRecord(null); setAddIntfForm({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' }); setAddIntfErrors({}); setIntfSourceSearchKeyword(''); setIntfTargetSearchKeyword(''); }} footer={null} width={760} closable title={editIntfRecord ? t('Edit Interface') : t('Add Interface')} styles={{ body: { padding: '32px 32px 24px' } }}>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5">
          <div className="space-y-4">
            <div>
              <div className="flex items-baseline gap-1 mb-1"><span className="text-red-500 text-sm">*</span><label className="text-sm text-gray-500">{t('Source App ID')}</label></div>
              <Select showSearch filterOption={false} style={{ width: '100%' }} placeholder={t('Search by App ID or Name')} value={addIntfForm.sourceAppId || undefined} status={addIntfErrors.sourceAppId ? 'error' : undefined} loading={intfSourceFetching} onSearch={(val) => setIntfSourceSearchKeyword(val)}
                onChange={(val) => { const hit = (intfSourceApps?.data ?? []).find((r: any) => r.appId === val); setAddIntfForm(f => ({ ...f, sourceAppId: val, applicationName: hit?.name ?? hit?.appFullName ?? '' })); setAddIntfErrors(e => ({ ...e, sourceAppId: undefined })); }}
                options={[ ...(addIntfForm.sourceAppId && !(intfSourceApps?.data ?? []).find((r: any) => r.appId === addIntfForm.sourceAppId) ? [{ value: addIntfForm.sourceAppId, label: `${addIntfForm.sourceAppId} - ${addIntfForm.applicationName || ''}` }] : []), ...(intfSourceApps?.data ?? []).map((r: any) => ({ value: r.appId, label: `${r.appId} - ${r.name || r.appFullName || ''}` })) ]}
                notFoundContent={intfSourceFetching ? t('Loading...') : t('No results')} />
              {addIntfErrors.sourceAppId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
            </div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Source App Name')}</label><Input value={addIntfForm.applicationName ?? ''} readOnly className="bg-gray-100" /></div>
            <div>
              <div className="flex items-baseline gap-1 mb-1"><span className="text-red-500 text-sm">*</span><label className="text-sm text-gray-500">{t('Target App ID')}</label></div>
              <Select showSearch filterOption={false} style={{ width: '100%' }} placeholder={t('Search by App ID or Name')} value={addIntfForm.targetAppId || undefined} status={addIntfErrors.targetAppId ? 'error' : undefined} loading={intfTargetFetching} onSearch={(val) => setIntfTargetSearchKeyword(val)}
                onChange={(val) => { const hit = (intfTargetApps?.data ?? []).find((r: any) => r.appId === val); setAddIntfForm(f => ({ ...f, targetAppId: val, targetAppName: hit?.name ?? hit?.appFullName ?? '' })); setAddIntfErrors(e => ({ ...e, targetAppId: undefined })); }}
                options={[ ...(addIntfForm.targetAppId && !(intfTargetApps?.data ?? []).find((r: any) => r.appId === addIntfForm.targetAppId) ? [{ value: addIntfForm.targetAppId, label: `${addIntfForm.targetAppId} - ${addIntfForm.targetAppName || ''}` }] : []), ...(intfTargetApps?.data ?? []).map((r: any) => ({ value: r.appId, label: `${r.appId} - ${r.name || r.appFullName || ''}` })) ]}
                notFoundContent={intfTargetFetching ? t('Loading...') : t('No results')} />
              {addIntfErrors.targetAppId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
            </div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Target App Name')}</label><Input value={addIntfForm.targetAppName ?? ''} readOnly className="bg-gray-100" /></div>
          </div>
          <div className="space-y-4">
            <div><label className="text-sm text-gray-500 block mb-1">{t('Business Object')}</label><Input value={addIntfForm.businessObject} onChange={(e) => setAddIntfForm(f => ({ ...f, businessObject: e.target.value }))} /></div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Interaction Type')}</label><Select style={{ width: '100%' }} value={addIntfForm.integrationType || undefined} onChange={(val) => setAddIntfForm(f => ({ ...f, integrationType: val }))} options={[{ value: 'Command', label: 'Command' }, { value: 'Event', label: 'Event' }, { value: 'Query', label: 'Query' }, { value: 'Embed', label: 'Embed' }]} /></div>
            <div><label className="text-sm text-gray-500 block mb-1">{t('Direction')}</label><Input value={addIntfForm.direction ?? ''} onChange={(e) => setAddIntfForm(f => ({ ...f, direction: e.target.value }))} /></div>
            <div>
              <div className="flex items-baseline gap-1 mb-1"><span className="text-red-500 text-sm">*</span><label className="text-sm text-gray-500">{t('Change Status')}</label></div>
              <Select style={{ width: '100%' }} value={addIntfForm.changeStatus || undefined} status={addIntfErrors.changeStatus ? 'error' : undefined} onChange={(val) => setAddIntfForm(f => ({ ...f, changeStatus: val }))} options={[{ value: 'New', label: 'New' }, { value: 'Keep', label: 'Keep' }, { value: 'Change', label: 'Change' }, { value: 'Sunset', label: 'Sunset' }, { value: '3rd Party', label: '3rd Party' }]} />
              {addIntfErrors.changeStatus && <div className="text-red-500 text-xs mt-0.5">Required</div>}
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button onClick={() => { setAddIntfOpen(false); setEditIntfRecord(null); setAddIntfForm({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' }); setAddIntfErrors({}); setIntfSourceSearchKeyword(''); setIntfTargetSearchKeyword(''); }}>{t('Cancel')}</Button>
          <Button type="primary" loading={editIntfRecord ? updateArchCheckInteraction.isPending : addArchCheckInteraction.isPending}
            onClick={() => {
              const errors: { sourceAppId?: string; targetAppId?: string; changeStatus?: string } = {};
              if (!addIntfForm.sourceAppId) errors.sourceAppId = "Required";
              if (!addIntfForm.targetAppId) errors.targetAppId = "Required";
              if (!addIntfForm.changeStatus) errors.changeStatus = "Required";
              if (Object.keys(errors).length > 0) { setAddIntfErrors(errors); return; }
              if (editIntfRecord) {
                updateArchCheckInteraction.mutate({ interactionUuid: editIntfRecord.checkAppUuid, sourceAppId: addIntfForm.sourceAppId, targetAppId: addIntfForm.targetAppId, interactionType: addIntfForm.integrationType || undefined, direction: addIntfForm.direction || undefined, businessObject: addIntfForm.businessObject || undefined, interfaceStatus: addIntfForm.changeStatus || undefined });
              } else {
                addArchCheckInteraction.mutate({ aiCheckId: aiDetail!._aiCheckId, sourceAppId: addIntfForm.sourceAppId, targetAppId: addIntfForm.targetAppId, interactionType: addIntfForm.integrationType || undefined, direction: addIntfForm.direction || undefined, businessObject: addIntfForm.businessObject || undefined, interfaceStatus: addIntfForm.changeStatus || undefined });
              }
            }}>{t('Save')}</Button>
        </div>
      </Modal>
    </>
  );
}

