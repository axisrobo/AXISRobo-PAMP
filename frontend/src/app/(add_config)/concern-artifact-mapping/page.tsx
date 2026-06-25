'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

type MappingItem = {
  id: string;
  concernKey: string;
  concernName: string;
  artifactKey: string;
  artifactName: string;
  defaultStatus: string;
  rationale: string | null;
  sortOrder: number;
  isActive: boolean;
};

const statusColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

export default function ConcernArtifactMappingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['concernArtifactMapping'],
    queryFn: () => api.get<{ data: MappingItem[]; total: number }>('/avdm/concern-artifact-mapping'),
  });

  const items = data?.data ?? [];

  const columns: ColumnsType<MappingItem> = [
    { title: 'Concern Key', dataIndex: 'concernKey', key: 'concernKey', width: 120, render: (v: string) => <strong>{v}</strong> },
    { title: 'Concern Name', dataIndex: 'concernName', key: 'concernName', width: 260 },
    { title: 'Artifact Key', dataIndex: 'artifactKey', key: 'artifactKey', width: 140 },
    { title: 'Artifact Name', dataIndex: 'artifactName', key: 'artifactName', width: 260 },
    {
      title: 'Status', dataIndex: 'defaultStatus', key: 'defaultStatus', width: 130,
      render: (v: string) => <Tag color={statusColor[v] || 'default'}>{v}</Tag>,
    },
    { title: 'Sort', dataIndex: 'sortOrder', key: 'sortOrder', width: 70 },
    {
      title: 'Active', dataIndex: 'isActive', key: 'isActive', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Yes' : 'No'}</Tag>,
    },
  ];

  return (
    <div className="p-6 space-y-4">
      <div>
        <Title level={4} style={{ marginBottom: 4 }}>Concern & Artifact Mapping</Title>
        <p className="text-sm text-text-secondary">Direct concern-to-artifact mapping from avdm_concern_artifact_mapping</p>
      </div>
      <Table
        columns={columns}
        dataSource={items}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (total) => `${total} mappings` }}
        size="small"
      />
    </div>
  );
}
