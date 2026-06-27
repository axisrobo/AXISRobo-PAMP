'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Input, Modal, Select, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react';
import { api } from '@/shared/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const statusColor: Record<string, string> = { draft: 'default', registered: 'blue', approved: 'green', restricted: 'orange', retired: 'red' };
const riskColor: Record<string, string> = { low: 'default', medium: 'blue', high: 'orange', critical: 'red' };
const approvalColor: Record<string, string> = { pending: 'default', approved: 'green', rejected: 'red' };
const stageColor: Record<string, string> = { sandbox: 'default', provenance_review: 'blue', aibom: 'purple', production: 'green' };

type Tool = {
  id: string; toolName: string; description: string; descriptionHash: string; signature: string;
  riskLevel: string; approvalStatus: string; lifecycleStage: string; notes: string;
};
type ServerDetail = {
  id: string; serverKey: string; name: string; description: string; owner: string; provider: string;
  transport: string; endpointUri: string; authMethod: string; provenanceSource: string; provenanceUri: string;
  scopes: string[]; status: string; tools: Tool[];
};
type Meta = {
  statuses: string[]; transports: string[]; authMethods: string[]; provenanceSources: string[];
  toolRiskLevels: string[]; toolApprovalStatuses: string[]; toolLifecycleStages: string[];
};

const emptyTool = {
  toolName: '', description: '', descriptionHash: '', signature: '',
  riskLevel: 'low', approvalStatus: 'pending', lifecycleStage: 'sandbox', notes: '',
};

export default function McpServerDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id as string;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [server, setServer] = useState({
    name: '', description: '', owner: '', provider: '', transport: 'stdio', endpointUri: '',
    authMethod: 'none', provenanceSource: '', provenanceUri: '', scopes: [] as string[], status: 'draft',
  });
  const [toolModalOpen, setToolModalOpen] = useState(false);
  const [editingToolId, setEditingToolId] = useState<string | null>(null);
  const [tool, setTool] = useState<typeof emptyTool>(emptyTool);

  const { data: meta } = useQuery({ queryKey: ['mcpMeta'], queryFn: () => api.get<Meta>('/mcp-servers/meta') });
  const { data } = useQuery({ queryKey: ['mcpServer', id], queryFn: () => api.get<ServerDetail>(`/mcp-servers/${id}`), enabled: !!id });

  useEffect(() => {
    if (data) {
      setServer({
        name: data.name, description: data.description, owner: data.owner, provider: data.provider,
        transport: data.transport, endpointUri: data.endpointUri, authMethod: data.authMethod,
        provenanceSource: data.provenanceSource, provenanceUri: data.provenanceUri, scopes: data.scopes, status: data.status,
      });
    }
  }, [data]);

  const serverMutation = useMutation({
    mutationFn: () => api.put(`/mcp-servers/${id}`, server),
    onSuccess: () => { messageApi.success('Server saved'); queryClient.invalidateQueries({ queryKey: ['mcpServer', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const toolMutation = useMutation({
    mutationFn: () => editingToolId
      ? api.put(`/mcp-servers/${id}/tools/${editingToolId}`, tool)
      : api.post(`/mcp-servers/${id}/tools`, tool),
    onSuccess: () => {
      messageApi.success(editingToolId ? 'Tool updated' : 'Tool added');
      setToolModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['mcpServer', id] });
    },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const delToolMutation = useMutation({
    mutationFn: (toolId: string) => api.delete(`/mcp-servers/${id}/tools/${toolId}`),
    onSuccess: () => { messageApi.success('Tool deleted'); queryClient.invalidateQueries({ queryKey: ['mcpServer', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const openCreateTool = () => { setEditingToolId(null); setTool(emptyTool); setToolModalOpen(true); };
  const openEditTool = (t: Tool) => {
    setEditingToolId(t.id);
    setTool({
      toolName: t.toolName, description: t.description, descriptionHash: t.descriptionHash, signature: t.signature,
      riskLevel: t.riskLevel, approvalStatus: t.approvalStatus, lifecycleStage: t.lifecycleStage, notes: t.notes,
    });
    setToolModalOpen(true);
  };

  const serverApprovalBlocked = server.status === 'approved' && !server.provenanceSource;
  const toolProductionBlocked = tool.lifecycleStage === 'production' && (tool.approvalStatus !== 'approved' || !tool.descriptionHash.trim());

  const columns: ColumnsType<Tool> = [
    {
      title: 'Tool', dataIndex: 'toolName', width: 200,
      render: (v: string, r) => <span><strong>{v}</strong>{r.lifecycleStage === 'production' ? <Tag color="green" className="ml-2">PROD</Tag> : null}</span>,
    },
    { title: 'Risk', dataIndex: 'riskLevel', width: 100, render: (v: string) => <Tag color={riskColor[v] || 'default'}>{v}</Tag> },
    { title: 'Approval', dataIndex: 'approvalStatus', width: 110, render: (v: string) => <Tag color={approvalColor[v] || 'default'}>{v}</Tag> },
    { title: 'Lifecycle', dataIndex: 'lifecycleStage', width: 150, render: (v: string) => <Tag color={stageColor[v] || 'default'}>{v}</Tag> },
    { title: 'Hash-pinned', dataIndex: 'descriptionHash', width: 160, ellipsis: true, render: (v: string) => v || '-' },
    {
      title: 'Action', key: 'action', width: 120,
      render: (_, r) => (
        <span className="flex gap-1">
          <Button type="link" size="small" onClick={() => openEditTool(r)}>Edit</Button>
          <Button type="link" size="small" danger icon={<Trash2 className="h-3.5 w-3.5" />} onClick={() => delToolMutation.mutate(r.id)} />
        </span>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center gap-3">
        <Button type="text" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => router.push('/mcp-servers')} />
        <Title level={4} style={{ marginBottom: 0 }}>{data?.name || 'MCP Server'}</Title>
        {data?.status && <Tag color={statusColor[data.status] || 'default'}>{data.status}</Tag>}
        {data?.serverKey && <Text type="secondary" className="text-xs">{data.serverKey}</Text>}
      </div>

      <Card title="MCP Server" size="small">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={server.name} onChange={(e) => setServer((p) => ({ ...p, name: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provider</div>
            <Input value={server.provider} onChange={(e) => setServer((p) => ({ ...p, provider: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Owner</div>
            <Input value={server.owner} onChange={(e) => setServer((p) => ({ ...p, owner: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Transport</div>
            <Select value={server.transport} onChange={(v) => setServer((p) => ({ ...p, transport: v }))} style={{ width: '100%' }}
              options={(meta?.transports || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Auth Method</div>
            <Select value={server.authMethod} onChange={(v) => setServer((p) => ({ ...p, authMethod: v }))} style={{ width: '100%' }}
              options={(meta?.authMethods || []).map((a) => ({ label: a, value: a }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provenance Source</div>
            <Select allowClear value={server.provenanceSource || undefined} onChange={(v) => setServer((p) => ({ ...p, provenanceSource: v || '' }))} style={{ width: '100%' }}
              options={(meta?.provenanceSources || []).map((s) => ({ label: s, value: s }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Endpoint URI</div>
            <Input value={server.endpointUri} onChange={(e) => setServer((p) => ({ ...p, endpointUri: e.target.value }))} placeholder="URL or stdio command" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Provenance URI</div>
            <Input value={server.provenanceUri} onChange={(e) => setServer((p) => ({ ...p, provenanceUri: e.target.value }))} placeholder="Origin repo / registry" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Status</div>
            <Select value={server.status} onChange={(v) => setServer((p) => ({ ...p, status: v }))} style={{ width: '100%' }}
              options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))} />
          </div>
        </div>

        <div className="mt-4">
          <div className="text-sm font-medium mb-1">Token Scopes (resource-indicator-scoped)</div>
          <Select mode="tags" value={server.scopes} onChange={(v) => setServer((p) => ({ ...p, scopes: v }))} style={{ width: '100%' }}
            placeholder="Add OAuth 2.1 resource scopes" tokenSeparators={[',', ' ']} />
        </div>
        <div className="mt-3">
          <div className="text-sm font-medium mb-1">Description</div>
          <TextArea value={server.description} onChange={(e) => setServer((p) => ({ ...p, description: e.target.value }))} rows={2} />
        </div>

        {serverApprovalBlocked && (
          <div className="mt-3"><Text type="danger" className="text-xs">Cannot approve: declare a provenance source before approving the MCP server.</Text></div>
        )}
        <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => serverMutation.mutate()}
          loading={serverMutation.isPending} disabled={!server.name.trim() || serverApprovalBlocked} className="mt-3">Save Server</Button>
      </Card>

      <Card
        title="Tools & Provenance" size="small"
        extra={<Button icon={<Plus className="h-4 w-4" />} onClick={openCreateTool}>Add Tool</Button>}
      >
        <Table columns={columns} dataSource={data?.tools ?? []} rowKey="id" pagination={false} size="small" />
      </Card>

      <Modal
        title={editingToolId ? 'Edit Tool' : 'Add Tool'} open={toolModalOpen} onCancel={() => setToolModalOpen(false)}
        onOk={() => toolMutation.mutate()} confirmLoading={toolMutation.isPending}
        okButtonProps={{ disabled: !tool.toolName.trim() || toolProductionBlocked }} width={600}
      >
        <div className="space-y-3 py-2">
          <div>
            <div className="text-sm font-medium mb-1">Tool Name</div>
            <Input value={tool.toolName} onChange={(e) => setTool((p) => ({ ...p, toolName: e.target.value }))} placeholder="e.g. create_issue, query_cmdb" />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Description</div>
            <TextArea value={tool.description} onChange={(e) => setTool((p) => ({ ...p, description: e.target.value }))} rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-sm font-medium mb-1">Description Hash (hash-pinned)</div>
              <Input value={tool.descriptionHash} onChange={(e) => setTool((p) => ({ ...p, descriptionHash: e.target.value }))} placeholder="sha256:..." />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Signature</div>
              <Input value={tool.signature} onChange={(e) => setTool((p) => ({ ...p, signature: e.target.value }))} placeholder="Signed tool description" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="text-sm font-medium mb-1">Risk Level</div>
              <Select value={tool.riskLevel} onChange={(v) => setTool((p) => ({ ...p, riskLevel: v }))} style={{ width: '100%' }}
                options={(meta?.toolRiskLevels || []).map((s) => ({ label: s, value: s }))} />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Approval</div>
              <Select value={tool.approvalStatus} onChange={(v) => setTool((p) => ({ ...p, approvalStatus: v }))} style={{ width: '100%' }}
                options={(meta?.toolApprovalStatuses || []).map((s) => ({ label: s, value: s }))} />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Lifecycle</div>
              <Select value={tool.lifecycleStage} onChange={(v) => setTool((p) => ({ ...p, lifecycleStage: v }))} style={{ width: '100%' }}
                options={(meta?.toolLifecycleStages || []).map((s) => ({ label: s, value: s }))} />
            </div>
          </div>
          {toolProductionBlocked && (
            <Text type="danger" className="text-xs">Promotion to production requires approval status &quot;approved&quot; and a hash-pinned description.</Text>
          )}
          <div>
            <div className="text-sm font-medium mb-1">Notes</div>
            <TextArea value={tool.notes} onChange={(e) => setTool((p) => ({ ...p, notes: e.target.value }))} rows={2} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
