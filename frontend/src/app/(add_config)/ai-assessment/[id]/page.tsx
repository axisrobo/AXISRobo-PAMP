'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Checkbox, Collapse, Input, message, Progress, Radio, Select, Space, Tag, Typography } from 'antd';
import { ArrowLeft, Save } from 'lucide-react';
import { api } from '@/shared/lib/api';

const { Title, Text, Paragraph } = Typography;

type MetaData = {
  adoptionTiers: Array<{ value: number; label: string; description: string }>;
  governanceMaturity: Array<{ value: number; label: string; description: string }>;
  scenarioClasses: Array<{ value: string; label: string }>;
  counterpartyTypes: Array<{ value: string; label: string }>;
  matrixLegend: Record<string, string>;
};

type AssessmentDetail = {
  id: string; projectName: string; status: string; createdBy: string;
  selfAssessment: { scenarioClass: string; counterpartyType: string; adoptionTier: number; governanceMaturity: number; matrixPosition: string; description: string } | null;
  checklist: Array<{ sectionKey: string; sectionLabel: string; itemKey: string; itemLabel: string; isChecked: boolean; isCritical: boolean; notes: string }>;
  checklistSummary: { total: number; checked: number; critical: number; criticalChecked: number; score: number };
};

const matrixColor: Record<string, string> = { CRITICAL: 'red', INSUFFICIENT: 'orange', HIGH_EXPOSURE: 'gold', FEASIBLE: 'blue', MANAGEABLE: 'green', MONITOR: 'default' };

export default function AiAssessmentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id as string;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();

  const [sa, setSa] = useState({ scenarioClass: 'enterprise', counterpartyType: 'cp1', adoptionTier: 1, governanceMaturity: 1, description: '' });
  const [checklistState, setChecklistState] = useState<Record<string, boolean>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({ queryKey: ['aiAssessment', id], queryFn: () => api.get<AssessmentDetail>(`/ai-assessment/${id}`), enabled: !!id });
  const { data: meta } = useQuery({ queryKey: ['aiAssessmentMeta'], queryFn: () => api.get<MetaData>('/ai-assessment/meta') });

  useEffect(() => {
    if (data?.selfAssessment) setSa(data.selfAssessment);
    if (data?.checklist) {
      const c: Record<string, boolean> = {};
      const n: Record<string, string> = {};
      data.checklist.forEach(i => { c[`${i.sectionKey}:${i.itemKey}`] = i.isChecked; n[`${i.sectionKey}:${i.itemKey}`] = i.notes || ''; });
      setChecklistState(c); setNotes(n);
    }
  }, [data]);

  const saMutation = useMutation({
    mutationFn: () => api.put(`/ai-assessment/${id}/self-assessment`, sa),
    onSuccess: (r: any) => { messageApi.success('Self-assessment saved. Matrix: ' + r.matrixPosition); queryClient.invalidateQueries({ queryKey: ['aiAssessment', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const clMutation = useMutation({
    mutationFn: () => {
      const items = Object.entries(checklistState).map(([k, v]) => { const [sk, ik] = k.split(':'); return { sectionKey: sk, itemKey: ik, isChecked: v, notes: notes[k] || '' }; });
      return api.put(`/ai-assessment/${id}/checklist`, { items });
    },
    onSuccess: () => { messageApi.success('Checklist saved'); queryClient.invalidateQueries({ queryKey: ['aiAssessment', id] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const sections = useMemo(() => {
    if (!data?.checklist) return [];
    const map = new Map<string, typeof data.checklist>();
    data.checklist.forEach(i => { const k = i.sectionKey; if (!map.has(k)) map.set(k, []); map.get(k)!.push(i); });
    return Array.from(map.entries());
  }, [data?.checklist]);

  const matrix = sa.adoptionTier && sa.governanceMaturity ? (data?.selfAssessment?.matrixPosition || '') : '';

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center gap-3">
        <Button type="text" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => router.push('/ai-assessment')} />
        <Title level={4} style={{ marginBottom: 0 }}>{data?.projectName || 'AI Project Self-Assessment'}</Title>
        {data?.status && <Tag color={data.status === 'reviewed' ? 'green' : 'default'}>{data.status}</Tag>}
      </div>

      {/* Self-Assessment Card */}
      <Card title="Self-Assessment" size="small">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium mb-1">Scenario Class</div>
            <Select value={sa.scenarioClass} onChange={v => setSa(p => ({ ...p, scenarioClass: v }))} style={{ width: '100%' }}
              options={(meta?.scenarioClasses || []).map(s => ({ label: s.label, value: s.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Counterparty Type</div>
            <Select value={sa.counterpartyType} onChange={v => setSa(p => ({ ...p, counterpartyType: v }))} style={{ width: '100%' }}
              options={(meta?.counterpartyTypes || []).map(s => ({ label: s.label, value: s.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Adoption Tier</div>
            <Select value={sa.adoptionTier} onChange={v => setSa(p => ({ ...p, adoptionTier: v }))} style={{ width: '100%' }}
              options={(meta?.adoptionTiers || []).map(t => ({ label: t.label, value: t.value }))} />
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Governance Maturity</div>
            <Select value={sa.governanceMaturity} onChange={v => setSa(p => ({ ...p, governanceMaturity: v }))} style={{ width: '100%' }}
              options={(meta?.governanceMaturity || []).map(t => ({ label: t.label, value: t.value }))} />
          </div>
        </div>
        {matrix && (
          <div className="mt-3 flex items-center gap-2">
            <Text strong>Matrix Position:</Text>
            <Tag color={matrixColor[matrix] || 'default'}>{matrix}</Tag>
            <Text type="secondary" className="text-xs">{meta?.matrixLegend?.[matrix]}</Text>
          </div>
        )}
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
          <div><Text strong>AT{sa.adoptionTier}:</Text> {meta?.adoptionTiers?.find(t => t.value === sa.adoptionTier)?.description}</div>
          <div><Text strong>L{sa.governanceMaturity}:</Text> {meta?.governanceMaturity?.find(t => t.value === sa.governanceMaturity)?.description}</div>
        </div>
        <div className="mt-3"><div className="text-sm font-medium mb-1">Description</div>
          <Input.TextArea value={sa.description} onChange={e => setSa(p => ({ ...p, description: e.target.value }))} rows={2} /></div>
        <Button type="primary" onClick={() => saMutation.mutate()} loading={saMutation.isPending} className="mt-3">Save Self-Assessment</Button>
      </Card>

      {/* Compliance Score */}
      {data?.checklistSummary && (
        <Card size="small">
          <div className="flex items-center gap-4">
            <Text strong>Architecture Review Checklist</Text>
            <Progress percent={data.checklistSummary.score} size="small" style={{ width: 200 }} />
            <Text type="secondary">{data.checklistSummary.checked}/{data.checklistSummary.total} checked ({data.checklistSummary.criticalChecked}/{data.checklistSummary.critical} critical)</Text>
            <Button icon={<Save className="h-4 w-4" />} onClick={() => clMutation.mutate()} loading={clMutation.isPending}>Save Checklist</Button>
          </div>
        </Card>
      )}

      {/* Checklist Sections */}
      <Collapse items={sections.map(([sk, items]) => {
        const checked = items.filter(i => checklistState[`${sk}:${i.itemKey}`]).length;
        const critical = items.filter(i => i.isCritical);
        const criticalChecked = critical.filter(i => checklistState[`${sk}:${i.itemKey}`]).length;
        return {
          key: sk, label: <span>{sk}. {items[0]?.sectionLabel} <Tag>{checked}/{items.length}</Tag> {critical.length > 0 && <Tag color="red">{criticalChecked}/{critical.length} critical</Tag>}</span>,
          children: (
            <div className="space-y-2">
              {items.map(item => (
                <div key={item.itemKey} className="flex items-start gap-3 py-1">
                  <Checkbox checked={checklistState[`${sk}:${item.itemKey}`] || false} onChange={e => setChecklistState(p => ({ ...p, [`${sk}:${item.itemKey}`]: e.target.checked }))} />
                  <div className="flex-1">
                    <Text>{item.itemLabel}</Text>
                    {item.isCritical && <Tag color="red" className="ml-2" style={{ fontSize: 10 }}>CRITICAL</Tag>}
                    <Input size="small" placeholder="Notes" value={notes[`${sk}:${item.itemKey}`] || ''} onChange={e => setNotes(p => ({ ...p, [`${sk}:${item.itemKey}`]: e.target.value }))} className="mt-1" />
                  </div>
                </div>
              ))}
            </div>
          ),
        };
      })} />
    </div>
  );
}
