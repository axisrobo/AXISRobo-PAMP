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

type ServerItem = {
  id: string; serverKey: string; name: string; provider: string; transport: string; authMethod: string;
  status: string; toolCount: number; productionToolCount: number; createdAt: string;
};
type Meta = {
  statuses: string[]; transports: string[]; authMethods: string[]; provenanceSources: string[];
  toolRiskLevels: string[]; toolApprovalStatuses: string[]; toolLifecycleStages: string[];
};

export default function McpGovernancePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: '', provider: '', transport: 'stdio', authMethod: 'none', status: 'draft' });

  const { data: meta } = useQuery({ queryKey: ['mcpMeta'], queryFn: () => api.get<Meta>('/mcp-servers/meta') });
  const { data, isLoading } = useQuery({
    queryKey: ['mcpServers', q, statusFilter],
    queryFn: () => api.get<{ data: ServerItem[]; total: number }>('/mcp-servers', { q, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post<{ id: string }>('/mcp-servers', form),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['mcpServers'] });
      setModalOpen(false);
      setForm({ name: '', provider: '', transport: 'stdio', authMethod: 'none', status: 'draft' });
      router.push(`/mcp-servers/${result.id}`);
    },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const columns: ColumnsType<ServerItem> = [
    {
      title: 'MCP Server', dataIndex: 'name', width: 240,
      render: (v: string, r) => (
        <div>
          <strong>{v}</strong>
          <div className="text-xs text-text-secondary">{r.serverKey}</div>
        </div>
      ),
    },
    { title: 'Provider', dataIndex: 'provider', width: 140, render: (v: string) => v || '-' },
    { title: 'Transport', dataIndex: 'transport', width: 120, render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Auth', dataIndex: 'authMethod', width: 130, render: (v: string) => <Tag>{v}</Tag> },
    {
      title: 'Tools', key: 'tools', width: 160,
      render: (_, r) => (
        <span>
          {r.toolCount}
          {r.productionToolCount > 0 ? <Tag color="green" className="ml-2">{r.productionToolCount} prod</Tag> : null}
        </span>
      ),
    },
    { title: 'Status', dataIndex: 'status', width: 110, render: (v: string) => <Tag color={statusColor[v] || 'default'}>{v}</Tag> },
    { title: 'Action', key: 'action', width: 90, render: (_, r) => <Button type="link" onClick={() => router.push(`/mcp-servers/${r.id}`)}>Open</Button> },
  ];

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>MCP Governance</Title>
          <p className="text-sm text-text-secondary">Register and govern MCP servers and their tools — provenance, approval, and production gating</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>New MCP Server</Button>
      </div>

      <div className="flex items-center gap-3">
        <Input.Search allowClear placeholder="Search name / key / provider" style={{ width: 320 }} onSearch={setQ} />
        <Select
          allowClear placeholder="Status" style={{ width: 180 }} value={statusFilter || undefined}
          onChange={(v) => setStatusFilter(v || '')}
          options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))}
        />
      </div>

      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal
        title="Register MCP Server" open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={() => createMutation.mutate()} confirmLoading={createMutation.isPending} okButtonProps={{ disabled: !form.name.trim() }}
      >
        <div className="space-y-3 py-2">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="e.g. github-mcp, internal-cmdb-mcp" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provider</div>
            <Input value={form.provider} onChange={(e) => setForm((p) => ({ ...p, provider: e.target.value }))} placeholder="Vendor / internal team" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Transport</div>
            <Select value={form.transport} onChange={(v) => setForm((p) => ({ ...p, transport: v }))} style={{ width: '100%' }}
              options={(meta?.transports || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Auth Method</div>
            <Select value={form.authMethod} onChange={(v) => setForm((p) => ({ ...p, authMethod: v }))} style={{ width: '100%' }}
              options={(meta?.authMethods || []).map((a) => ({ label: a, value: a }))} />
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
