'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Input, Modal, Select, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

const statusColor: Record<string, string> = { draft: 'default', registered: 'blue', approved: 'green', restricted: 'orange', retired: 'red' };

type AgentItem = {
  id: string; agentKey: string; name: string; agentType: string; owner: string;
  scenarioClass: string; autonomyLevel: string; trustLevel: string; status: string;
  modelName: string | null; createdAt: string;
};
type Meta = {
  agentTypes: string[]; autonomyLevels: string[]; trustLevels: string[]; statuses: string[];
  capabilities: { value: string; label: string }[];
  scenarioClasses: { value: string; label: string }[];
  counterpartyTypes: { value: string; label: string }[];
  adoptionTiers: { value: number; label: string; description: string }[];
  lethalTrifecta: string[];
};

export default function AiAgentRegistryPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: '', agentType: 'assistant', owner: '', scenarioClass: 'enterprise', status: 'draft' });

  const { data: meta } = useQuery({ queryKey: ['aiAgentMeta'], queryFn: () => api.get<Meta>('/ai-agents/meta') });
  const { data, isLoading } = useQuery({
    queryKey: ['aiAgents', q, statusFilter],
    queryFn: () => api.get<{ data: AgentItem[]; total: number }>('/ai-agents', { q, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post<{ id: string }>('/ai-agents', form),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['aiAgents'] });
      setModalOpen(false);
      setForm({ name: '', agentType: 'assistant', owner: '', scenarioClass: 'enterprise', status: 'draft' });
      router.push(`/ai-agents/${result.id}`);
    },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const columns: ColumnsType<AgentItem> = [
    {
      title: 'Agent', dataIndex: 'name', width: 240,
      render: (v: string, r) => (
        <div>
          <strong>{v}</strong>
          <div className="text-xs text-text-secondary">{r.agentKey}</div>
        </div>
      ),
    },
    { title: 'Type', dataIndex: 'agentType', width: 120, render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Scenario', dataIndex: 'scenarioClass', width: 120 },
    { title: 'Autonomy', dataIndex: 'autonomyLevel', width: 140 },
    { title: 'Trust', dataIndex: 'trustLevel', width: 110 },
    { title: 'Model', dataIndex: 'modelName', width: 160, render: (v: string | null) => v || '-' },
    { title: 'Status', dataIndex: 'status', width: 110, render: (v: string) => <Tag color={statusColor[v] || 'default'}>{v}</Tag> },
    { title: 'Action', key: 'action', width: 90, render: (_, r) => <Button type="link" onClick={() => router.push(`/ai-agents/${r.id}`)}>Open</Button> },
  ];

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>Agent Registry</Title>
          <p className="text-sm text-text-secondary">Register and govern AI agents as governed architecture elements (design-time governance, not runtime identity)</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>New Agent</Button>
      </div>

      <div className="flex items-center gap-3">
        <Input.Search allowClear placeholder="Search name / key / owner" style={{ width: 320 }} onSearch={setQ} />
        <Select
          allowClear placeholder="Status" style={{ width: 180 }} value={statusFilter || undefined}
          onChange={(v) => setStatusFilter(v || '')}
          options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))}
        />
      </div>

      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal
        title="Register AI Agent" open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={() => createMutation.mutate()} confirmLoading={createMutation.isPending} okButtonProps={{ disabled: !form.name.trim() }}
      >
        <div className="space-y-3 py-2">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="e.g. Procurement Copilot" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Type</div>
            <Select value={form.agentType} onChange={(v) => setForm((p) => ({ ...p, agentType: v }))} style={{ width: '100%' }}
              options={(meta?.agentTypes || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Owner</div>
            <Input value={form.owner} onChange={(e) => setForm((p) => ({ ...p, owner: e.target.value }))} placeholder="Owning team / person" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Scenario Class</div>
            <Select value={form.scenarioClass} onChange={(v) => setForm((p) => ({ ...p, scenarioClass: v }))} style={{ width: '100%' }}
              options={(meta?.scenarioClasses || []).map((s) => ({ label: s.label, value: s.value }))} />
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
