'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Input, Modal, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Plus } from 'lucide-react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

type AssessmentItem = { id: string; projectName: string; projectIdRef: string; status: string; createdBy: string; createdAt: string };

export default function AiAssessmentListPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [creating, setCreating] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['aiAssessments'],
    queryFn: () => api.get<{ data: AssessmentItem[]; total: number }>('/ai-assessment'),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post('/ai-assessment', { projectName, projectIdRef: '' }),
    onSuccess: (result: any) => {
      queryClient.invalidateQueries({ queryKey: ['aiAssessments'] });
      setModalOpen(false);
      setProjectName('');
      router.push(`/ai-assessment/${result.id}`);
    },
  });

  const columns: ColumnsType<AssessmentItem> = [
    { title: 'Project Name', dataIndex: 'projectName', width: 280, render: (v: string) => <strong>{v}</strong> },
    { title: 'Project Ref', dataIndex: 'projectIdRef', width: 160 },
    { title: 'Status', dataIndex: 'status', width: 100, render: (v: string) => <Tag color={v === 'reviewed' ? 'green' : v === 'draft' ? 'default' : 'blue'}>{v}</Tag> },
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
          <p className="text-sm text-text-secondary">Assess AI projects against the Enterprise AI Security Architecture Guideline v2.4</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>New Assessment</Button>
      </div>
      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal title="New AI Project Assessment" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => { setCreating(true); createMutation.mutate(); }} confirmLoading={creating}>
        <div className="space-y-3 py-2">
          <div><label className="text-sm font-medium">Project Name</label></div>
          <Input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Enter AI project name" />
        </div>
      </Modal>
    </div>
  );
}
