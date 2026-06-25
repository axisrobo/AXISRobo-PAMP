'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

type MappingItem = {
  concernKey: string;
  concernName: string;
  concernLayer: string;
  viewpointNumber: number;
  viewpointName: string;
  viewpointLayer: string;
};

export default function ConcernViewpointMappingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['concernViewpointMapping'],
    queryFn: () => api.get<{ data: MappingItem[]; total: number }>('/avdm/concern-viewpoint-mapping'),
  });

  const items = data?.data ?? [];

  const columns: ColumnsType<MappingItem> = [
    { title: 'Concern Key', dataIndex: 'concernKey', width: 110, render: (v: string) => <strong>{v}</strong> },
    { title: 'Concern Name', dataIndex: 'concernName', width: 260 },
    { title: 'Concern Layer', dataIndex: 'concernLayer', width: 180 },
    { title: 'VP #', dataIndex: 'viewpointNumber', width: 60 },
    { title: 'Viewpoint Name', dataIndex: 'viewpointName', width: 280 },
    { title: 'Viewpoint Layer', dataIndex: 'viewpointLayer', width: 180, render: (v: string) => <Tag>{v}</Tag> },
  ];

  return (
    <div className="p-6 space-y-4">
      <div>
        <Title level={4} style={{ marginBottom: 4 }}>Concern & Viewpoint Mapping</Title>
        <p className="text-sm text-text-secondary">Which concerns each architecture viewpoint addresses</p>
      </div>
      <Table
        columns={columns}
        dataSource={items}
        rowKey={(r) => `${r.concernKey}-${r.viewpointNumber}`}
        loading={isLoading}
        pagination={{ pageSize: 100, showTotal: (total) => `${total} mappings` }}
        size="small"
      />
    </div>
  );
}
