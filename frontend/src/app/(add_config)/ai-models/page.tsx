'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Input, Modal, Select, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

const statusColor: Record<string, string> = { draft: 'default', approved: 'green', restricted: 'orange', retired: 'red' };

type ModelItem = {
  id: string; modelKey: string; name: string; provider: string; modelType: string;
  status: string; versionCount: number; productionVersion: string | null; createdBy: string; createdAt: string;
};
type Meta = { modelTypes: string[]; statuses: string[]; provenanceSources: string[]; approvalStatuses: string[] };

export default function AiModelRegistryPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: '', provider: '', modelType: 'llm', owner: '', status: 'draft' });

  const { data: meta } = useQuery({ queryKey: ['aiModelMeta'], queryFn: () => api.get<Meta>('/ai-models/meta') });
  const { data, isLoading } = useQuery({
    queryKey: ['aiModels', q, statusFilter],
    queryFn: () => api.get<{ data: ModelItem[]; total: number }>('/ai-models', { q, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post<{ id: string }>('/ai-models', form),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['aiModels'] });
      setModalOpen(false);
      setForm({ name: '', provider: '', modelType: 'llm', owner: '', status: 'draft' });
      router.push(`/ai-models/${result.id}`);
    },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const columns: ColumnsType<ModelItem> = [
    {
      title: 'Model', dataIndex: 'name', width: 260,
      render: (v: string, r) => (
        <div>
          <strong>{v}</strong>
          <div className="text-xs text-text-secondary">{r.modelKey}</div>
        </div>
      ),
    },
    { title: 'Provider', dataIndex: 'provider', width: 140, render: (v: string) => v || '-' },
    { title: 'Type', dataIndex: 'modelType', width: 120, render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Status', dataIndex: 'status', width: 110, render: (v: string) => <Tag color={statusColor[v] || 'default'}>{v}</Tag> },
    {
      title: 'Versions', key: 'versions', width: 160,
      render: (_, r) => (
        <span>
          {r.versionCount}
          {r.productionVersion ? <Tag color="green" className="ml-2">prod: {r.productionVersion}</Tag> : null}
        </span>
      ),
    },
    { title: 'Created At', dataIndex: 'createdAt', width: 140, render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: 'Action', key: 'action', width: 90, render: (_, r) => <Button type="link" onClick={() => router.push(`/ai-models/${r.id}`)}>Open</Button> },
  ];

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>AI Model Registry</Title>
          <p className="text-sm text-text-secondary">Register AI models with version and provenance tracking</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>New Model</Button>
      </div>

      <div className="flex items-center gap-3">
        <Input.Search allowClear placeholder="Search name / provider / key" style={{ width: 320 }} onSearch={setQ} />
        <Select
          allowClear placeholder="Status" style={{ width: 180 }} value={statusFilter || undefined}
          onChange={(v) => setStatusFilter(v || '')}
          options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))}
        />
      </div>

      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal
        title="New AI Model" open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={() => createMutation.mutate()} confirmLoading={createMutation.isPending} okButtonProps={{ disabled: !form.name.trim() }}
      >
        <div className="space-y-3 py-2">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="e.g. GPT-4o, internal-rerank-v1" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provider</div>
            <Input value={form.provider} onChange={(e) => setForm((p) => ({ ...p, provider: e.target.value }))} placeholder="e.g. OpenAI, Anthropic, internal" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Type</div>
            <Select value={form.modelType} onChange={(v) => setForm((p) => ({ ...p, modelType: v }))} style={{ width: '100%' }}
              options={(meta?.modelTypes || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Owner</div>
            <Input value={form.owner} onChange={(e) => setForm((p) => ({ ...p, owner: e.target.value }))} placeholder="Owning team / person" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Status</div>
            <Select value={form.status} onChange={(v) => setForm((p) => ({ ...p, status: v }))} style={{ width: '100%' }}
              options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
