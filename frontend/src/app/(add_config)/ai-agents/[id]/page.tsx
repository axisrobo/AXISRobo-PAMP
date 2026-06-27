'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Input, Select, Switch, Tag, Typography, message } from 'antd';
import { ArrowLeft, Save } from 'lucide-react';
import { api } from '@/shared/lib/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const statusColor: Record<string, string> = { draft: 'default', registered: 'blue', approved: 'green', restricted: 'orange', retired: 'red' };

type AgentDetail = {
  id: string; agentKey: string; name: string; agentType: string; description: string; owner: string;
  scenarioClass: string; counterpartyType: string; adoptionTier: number; autonomyLevel: string; trustLevel: string;
  hitlRequired: boolean; capabilities: string[]; modelIdRef: string | null; modelName: string | null; status: string;
};
type Meta = {
  agentTypes: string[]; autonomyLevels: string[]; trustLevels: string[]; statuses: string[];
  capabilities: { value: string; label: string }[];
  scenarioClasses: { value: string; label: string }[];
  counterpartyTypes: { value: string; label: string }[];
  adoptionTiers: { value: number; label: string; description: string }[];
  lethalTrifecta: string[];
};

export default function AiAgentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id as string;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [agent, setAgent] = useState({
    name: '', agentType: 'assistant', description: '', owner: '',
    scenarioClass: 'enterprise', counterpartyType: 'cp1', adoptionTier: 1,
    autonomyLevel: 'human_approval', trustLevel: 'limited', hitlRequired: false,
    capabilities: [] as string[], modelIdRef: '', status: 'draft',
  });

  const { data: meta } = useQuery({ queryKey: ['aiAgentMeta'], queryFn: () => api.get<Meta>('/ai-agents/meta') });
  const { data } = useQuery({ queryKey: ['aiAgent', id], queryFn: () => api.get<AgentDetail>(`/ai-agents/${id}`), enabled: !!id });
  const { data: models } = useQuery({
    queryKey: ['aiModelOptions'],
    queryFn: () => api.get<{ data: { id: string; name: string }[] }>('/ai-models', { pageSize: 100 }),
  });

  useEffect(() => {
    if (data) {
      setAgent({
        name: data.name, agentType: data.agentType, description: data.description, owner: data.owner,
        scenarioClass: data.scenarioClass, counterpartyType: data.counterpartyType, adoptionTier: data.adoptionTier,
        autonomyLevel: data.autonomyLevel, trustLevel: data.trustLevel, hitlRequired: data.hitlRequired,
        capabilities: data.capabilities, modelIdRef: data.modelIdRef || '', status: data.status,
      });
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () => api.put(`/ai-agents/${id}`, agent),
    onSuccess: () => { messageApi.success('Agent saved'); queryClient.invalidateQueries({ queryKey: ['aiAgent', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const trifecta = meta?.lethalTrifecta ?? [];
  const hasTrifecta = trifecta.length > 0 && trifecta.every((c) => agent.capabilities.includes(c));
  const approvalBlocked = agent.status === 'approved' && hasTrifecta && !agent.hitlRequired;

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center gap-3">
        <Button type="text" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => router.push('/ai-agents')} />
        <Title level={4} style={{ marginBottom: 0 }}>{data?.name || 'AI Agent'}</Title>
        {data?.status && <Tag color={statusColor[data.status] || 'default'}>{data.status}</Tag>}
        {data?.agentKey && <Text type="secondary" className="text-xs">{data.agentKey}</Text>}
      </div>

      <Card title="Agent Governance" size="small">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm font-medium mb-1">Name</div>
            <Input value={agent.name} onChange={(e) => setAgent((p) => ({ ...p, name: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Type</div>
            <Select value={agent.agentType} onChange={(v) => setAgent((p) => ({ ...p, agentType: v }))} style={{ width: '100%' }}
              options={(meta?.agentTypes || []).map((t) => ({ label: t, value: t }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Owner</div>
            <Input value={agent.owner} onChange={(e) => setAgent((p) => ({ ...p, owner: e.target.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Scenario Class</div>
            <Select value={agent.scenarioClass} onChange={(v) => setAgent((p) => ({ ...p, scenarioClass: v }))} style={{ width: '100%' }}
              options={(meta?.scenarioClasses || []).map((s) => ({ label: s.label, value: s.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Counterparty Type</div>
            <Select value={agent.counterpartyType} onChange={(v) => setAgent((p) => ({ ...p, counterpartyType: v }))} style={{ width: '100%' }}
              options={(meta?.counterpartyTypes || []).map((s) => ({ label: s.label, value: s.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Adoption Tier</div>
            <Select value={agent.adoptionTier} onChange={(v) => setAgent((p) => ({ ...p, adoptionTier: v }))} style={{ width: '100%' }}
              options={(meta?.adoptionTiers || []).map((t) => ({ label: t.label, value: t.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Autonomy Level</div>
            <Select value={agent.autonomyLevel} onChange={(v) => setAgent((p) => ({ ...p, autonomyLevel: v }))} style={{ width: '100%' }}
              options={(meta?.autonomyLevels || []).map((s) => ({ label: s, value: s }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Trust Level</div>
            <Select value={agent.trustLevel} onChange={(v) => setAgent((p) => ({ ...p, trustLevel: v }))} style={{ width: '100%' }}
              options={(meta?.trustLevels || []).map((s) => ({ label: s, value: s }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Linked Model</div>
            <Select allowClear value={agent.modelIdRef || undefined} onChange={(v) => setAgent((p) => ({ ...p, modelIdRef: v || '' }))} style={{ width: '100%' }}
              placeholder="Governed model used by this agent"
              options={(models?.data || []).map((m) => ({ label: m.name, value: m.id }))} />
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="md:col-span-2">
            <div className="text-sm font-medium mb-1">Capabilities</div>
            <Select mode="multiple" value={agent.capabilities} onChange={(v) => setAgent((p) => ({ ...p, capabilities: v }))} style={{ width: '100%' }}
              placeholder="Governed capability flags" options={(meta?.capabilities || []).map((c) => ({ label: c.label, value: c.value }))} />
          </div>
          <div className="flex items-center gap-2 pb-1">
            <Switch checked={agent.hitlRequired} onChange={(v) => setAgent((p) => ({ ...p, hitlRequired: v }))} />
            <span className="text-sm">Human-in-the-Loop required</span>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="text-sm font-medium mb-1">Status</div>
            <Select value={agent.status} onChange={(v) => setAgent((p) => ({ ...p, status: v }))} style={{ width: '100%' }}
              options={(meta?.statuses || []).map((s) => ({ label: s, value: s }))} />
          </div>
          <div className="md:col-span-2">
            <div className="text-sm font-medium mb-1">Description</div>
            <TextArea value={agent.description} onChange={(e) => setAgent((p) => ({ ...p, description: e.target.value }))} rows={2} />
          </div>
        </div>

        {hasTrifecta && (
          <div className="mt-3">
            <Tag color="red">Lethal Trifecta</Tag>
            <Text type="secondary" className="text-xs">Private data + untrusted content + external communication are all enabled.</Text>
          </div>
        )}
        {approvalBlocked && (
          <div className="mt-2">
            <Text type="danger" className="text-xs">Cannot approve: lethal trifecta capabilities require Human-in-the-Loop. Enable HITL or change status.</Text>
          </div>
        )}

        <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => saveMutation.mutate()}
          loading={saveMutation.isPending} disabled={!agent.name.trim() || approvalBlocked} className="mt-4">Save Agent</Button>
      </Card>
    </div>
  );
}
