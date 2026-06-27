'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Modal, Select, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

const statusColor: Record<string, string> = { approved: 'green', conditional: 'gold', blocked: 'red', draft: 'default', reviewed: 'green' };

type AssessmentItem = { id: string; projectName: string; projectIdRef: string; status: string; createdBy: string; createdAt: string };
type ProjectOption = { id: string; projectId: string; projectName: string };

export default function AiAssessmentListPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [projectId, setProjectId] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['aiAssessments'],
    queryFn: () => api.get<{ data: AssessmentItem[]; total: number }>('/ai-assessment'),
  });

  const { data: projectsData } = useQuery({
    queryKey: ['aiAssessmentProjects'],
    queryFn: () => api.get<{ data: ProjectOption[] }>('/projects', { page: 1, pageSize: 100 }),
  });
  const projects = projectsData?.data ?? [];

  const createMutation = useMutation({
    mutationFn: () => {
      const proj = projects.find((p) => p.projectId === projectId);
      return api.post<{ id: string }>('/ai-assessment', {
        projectName: proj?.projectName || '',
        projectIdRef: proj?.projectId || '',
      });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['aiAssessments'] });
      setModalOpen(false);
      setProjectId('');
      router.push(`/ai-assessment/${result.id}`);
    },
  });

  const columns: ColumnsType<AssessmentItem> = [
    { title: 'Project Name', dataIndex: 'projectName', width: 280, render: (v: string) => <strong>{v}</strong> },
    { title: 'Project Ref', dataIndex: 'projectIdRef', width: 160 },
    { title: 'Status', dataIndex: 'status', width: 100, render: (v: string) => <Tag color={statusColor[v] || 'blue'}>{v}</Tag> },
    { title: 'Created By', dataIndex: 'createdBy', width: 140 },
    { title: 'Created At', dataIndex: 'createdAt', width: 180, render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    {
      title: 'Action', key: 'action', width: 100,
      render: (_, r) => <Button type="link" onClick={() => router.push(`/ai-assessment/${r.id}`)}>Open</Button>,
    },
  ];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>AI Project Self-Assessment</Title>
          <p className="text-sm text-text-secondary">Assess AI projects with adoption-tier × governance-maturity scoring</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>New Assessment</Button>
      </div>
      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal title="New AI Project Assessment" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => createMutation.mutate()} confirmLoading={createMutation.isPending} okButtonProps={{ disabled: !projectId }}>
        <div className="space-y-3 py-2">
          <div><label className="text-sm font-medium">Project</label></div>
          <Select showSearch value={projectId || undefined} onChange={(v) => setProjectId(v)} style={{ width: '100%' }}
            placeholder="Select a project" optionFilterProp="label"
            options={projects.map((p) => ({ label: `${p.projectId} — ${p.projectName}`, value: p.projectId }))} />
        </div>
      </Modal>
    </div>
  );
}
