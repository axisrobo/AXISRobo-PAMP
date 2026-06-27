'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Input, Modal, Select, Switch, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react';
import { api } from '@/shared/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const statusColor: Record<string, string> = { draft: 'default', approved: 'green', restricted: 'orange', retired: 'red' };
const approvalColor: Record<string, string> = { pending: 'default', approved: 'green', rejected: 'red' };

type Version = {
  id: string; version: string; source: string; sourceUri: string; checksum: string; license: string;
  trainingDataProvenance: string; approvalStatus: string; isProduction: boolean; notes: string; createdAt: string;
};
type ModelDetail = {
  id: string; modelKey: string; name: string; provider: string; modelType: string; description: string;
  owner: string; status: string; versions: Version[];
};
type Meta = { modelTypes: string[]; statuses: string[]; provenanceSources: string[]; approvalStatuses: string[] };

const emptyVersion = {
  version: '', source: '', sourceUri: '', checksum: '', license: '',
  trainingDataProvenance: '', approvalStatus: 'pending', isProduction: false, notes: '',
};

export default function AiModelDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id as string;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [model, setModel] = useState({ name: '', provider: '', modelType: 'llm', owner: '', status: 'draft', description: '' });
  const [verModalOpen, setVerModalOpen] = useState(false);
  const [editingVerId, setEditingVerId] = useState<string | null>(null);
  const [ver, setVer] = useState<typeof emptyVersion>(emptyVersion);

  const { data: meta } = useQuery({ queryKey: ['aiModelMeta'], queryFn: () => api.get<Meta>('/ai-models/meta') });
  const { data } = useQuery({ queryKey: ['aiModel', id], queryFn: () => api.get<ModelDetail>(`/ai-models/${id}`), enabled: !!id });

  useEffect(() => {
    if (data) {
      setModel({
        name: data.name, provider: data.provider, modelType: data.modelType,
        owner: data.owner, status: data.status, description: data.description,
      });
    }
  }, [data]);

  const modelMutation = useMutation({
    mutationFn: () => api.put(`/ai-models/${id}`, model),
    onSuccess: () => { messageApi.success('Model saved'); queryClient.invalidateQueries({ queryKey: ['aiModel', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const verMutation = useMutation({
    mutationFn: () => editingVerId
      ? api.put(`/ai-models/${id}/versions/${editingVerId}`, ver)
      : api.post(`/ai-models/${id}/versions`, ver),
    onSuccess: () => {
      messageApi.success(editingVerId ? 'Version updated' : 'Version added');
      setVerModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['aiModel', id] });
    },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const delVerMutation = useMutation({
    mutationFn: (versionId: string) => api.delete(`/ai-models/${id}/versions/${versionId}`),
    onSuccess: () => { messageApi.success('Version deleted'); queryClient.invalidateQueries({ queryKey: ['aiModel', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const openCreateVersion = () => { setEditingVerId(null); setVer(emptyVersion); setVerModalOpen(true); };
  const openEditVersion = (v: Version) => {
    setEditingVerId(v.id);
    setVer({
      version: v.version, source: v.source, sourceUri: v.sourceUri, checksum: v.checksum, license: v.license,
      trainingDataProvenance: v.trainingDataProvenance, approvalStatus: v.approvalStatus, isProduction: v.isProduction, notes: v.notes,
    });
    setVerModalOpen(true);
  };

  const columns: ColumnsType<Version> = [
    {
      title: 'Version', dataIndex: 'version', width: 160,
      render: (v: string, r) => <span><strong>{v}</strong>{r.isProduction ? <Tag color="green" className="ml-2">PRODUCTION</Tag> : null}</span>,
    },
    { title: 'Source', dataIndex: 'source', width: 140, render: (v: string) => v ? <Tag>{v}</Tag> : '-' },
    { title: 'Approval', dataIndex: 'approvalStatus', width: 110, render: (v: string) => <Tag color={approvalColor[v] || 'default'}>{v}</Tag> },
    { title: 'Checksum', dataIndex: 'checksum', width: 160, ellipsis: true, render: (v: string) => v || '-' },
    { title: 'License', dataIndex: 'license', width: 120, render: (v: string) => v || '-' },
    {
      title: 'Action', key: 'action', width: 120,
      render: (_, r) => (
        <span className="flex gap-1">
          <Button type="link" size="small" onClick={() => openEditVersion(r)}>Edit</Button>
          <Button type="link" size="small" danger icon={<Trash2 className="h-3.5 w-3.5" />} onClick={() => delVerMutation.mutate(r.id)} />
        </span>
      ),
    },
  ];

  const productionBlocked = ver.isProduction && ver.approvalStatus !== 'approved';

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center gap-3">
        <Button type="text" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => router.push('/ai-models')} />
        <Title level={4} style={{ marginBottom: 0 }}>{data?.name || 'AI Model'}</Title>
        {data?.status && <Tag color={statusColor[data.status] || 'default'}>{data.status}</Tag>}
        {data?.modelKey && <Text type="secondary" className="text-xs">{data.modelKey}</Text>}
      </div>

      <Card title="Model" size="small">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={model.name} onChange={(e) => setModel((p) => ({ ...p, name: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provider</div>
            <Input value={model.provider} onChange={(e) => setModel((p) => ({ ...p, provider: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Type</div>
            <Select value={model.modelType} onChange={(v) => setModel((p) => ({ ...p, modelType: v }))} style={{ width: '100%' }}
              options={(meta?.modelTypes || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Owner</div>
            <Input value={model.owner} onChange={(e) => setModel((p) => ({ ...p, owner: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Status</div>
            <Select value={model.status} onChange={(v) => setModel((p) => ({ ...p, status: v }))} style={{ width: '100%' }}
              options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))} />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-sm font-medium mb-1">Description</div>
          <TextArea value={model.description} onChange={(e) => setModel((p) => ({ ...p, description: e.target.value }))} rows={2} />
        </div>
        <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => modelMutation.mutate()} loading={modelMutation.isPending} className="mt-3">Save Model</Button>
      </Card>

      <Card
        title="Versions & Provenance" size="small"
        extra={<Button icon={<Plus className="h-4 w-4" />} onClick={openCreateVersion}>Add Version</Button>}
      >
        <Table columns={columns} dataSource={data?.versions ?? []} rowKey="id" pagination={false} size="small" />
      </Card>

      <Modal
        title={editingVerId ? 'Edit Version' : 'Add Version'} open={verModalOpen} onCancel={() => setVerModalOpen(false)}
        onOk={() => verMutation.mutate()} confirmLoading={verMutation.isPending}
        okButtonProps={{ disabled: !ver.version.trim() || productionBlocked }} width={600}
      >
        <div className="space-y-3 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-sm font-medium mb-1">Version</div>
              <Input value={ver.version} onChange={(e) => setVer((p) => ({ ...p, version: e.target.value }))} placeholder="e.g. 1.0.0, 2024-08-06" />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Provenance Source</div>
              <Select allowClear value={ver.source || undefined} onChange={(v) => setVer((p) => ({ ...p, source: v || '' }))} style={{ width: '100%' }}
                options={(meta?.provenanceSources || []).map((s) => ({ label: s, value: s }))} />
            </div>
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Source URI</div>
            <Input value={ver.sourceUri} onChange={(e) => setVer((p) => ({ ...p, sourceUri: e.target.value }))} placeholder="Registry path / URL / repo" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-sm font-medium mb-1">Checksum / Digest</div>
              <Input value={ver.checksum} onChange={(e) => setVer((p) => ({ ...p, checksum: e.target.value }))} placeholder="sha256:..." />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">License</div>
              <Input value={ver.license} onChange={(e) => setVer((p) => ({ ...p, license: e.target.value }))} placeholder="e.g. Apache-2.0, proprietary" />
            </div>
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Training Data Provenance</div>
            <TextArea value={ver.trainingDataProvenance} onChange={(e) => setVer((p) => ({ ...p, trainingDataProvenance: e.target.value }))} rows={2} placeholder="Corpus origin, licensing, PII handling" />
          </div>
          <div className="grid grid-cols-2 gap-3 items-end">
            <div>
              <div className="text-sm font-medium mb-1">Approval Status</div>
              <Select value={ver.approvalStatus} onChange={(v) => setVer((p) => ({ ...p, approvalStatus: v }))} style={{ width: '100%' }}
                options={(meta?.approvalStatuses || []).map((s) => ({ label: s, value: s }))} />
            </div>
            <div className="flex items-center gap-2 pb-1">
              <Switch checked={ver.isProduction} onChange={(v) => setVer((p) => ({ ...p, isProduction: v }))} />
              <span className="text-sm">Production</span>
            </div>
          </div>
          {productionBlocked && (
            <Text type="danger" className="text-xs">A version must be approved before it can be marked production (production gating).</Text>
          )}
          <div>
            <div className="text-sm font-medium mb-1">Notes</div>
            <TextArea value={ver.notes} onChange={(e) => setVer((p) => ({ ...p, notes: e.target.value }))} rows={2} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
