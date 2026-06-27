'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, Tag, Typography, Checkbox } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useState } from 'react';
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
  const [includeUnmapped, setIncludeUnmapped] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['concernViewpointMapping', includeUnmapped],
    queryFn: () => api.get<{ data: MappingItem[]; total: number }>('/avdm/concern-viewpoint-mapping', { includeUnmapped }),
  });

  const items = data?.data ?? [];
  const unmappedCount = includeUnmapped ? items.filter((i) => !i.viewpointName).length : 0;

  const columns: ColumnsType<MappingItem> = [
    { title: 'Concern Key', dataIndex: 'concernKey', width: 110, render: (v: string) => <strong>{v}</strong>, sorter: (a, b) => a.concernKey.localeCompare(b.concernKey), defaultSortOrder: 'ascend' },
    { title: 'Concern Name', dataIndex: 'concernName', width: 260 },
    { title: 'Concern Layer', dataIndex: 'concernLayer', width: 180 },
    { title: 'VP #', dataIndex: 'viewpointNumber', width: 60, render: (v: number) => (v > 0 ? v : '') },
    { title: 'Viewpoint Name', dataIndex: 'viewpointName', width: 280, render: (v: string) => v || <span className="text-red-400 italic">no mapping</span> },
    { title: 'Viewpoint Layer', dataIndex: 'viewpointLayer', width: 180, render: (v: string) => v ? <Tag>{v}</Tag> : <Tag color="red">unmapped</Tag> },
  ];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>Concern & Viewpoint Mapping</Title>
          <p className="text-sm text-text-secondary">Sorted by Concern Key — each concern mapped to its viewpoint(s)</p>
        </div>
        <Checkbox checked={includeUnmapped} onChange={(e) => setIncludeUnmapped(e.target.checked)}>
          Show unmapped concerns
          {includeUnmapped && unmappedCount > 0 && (
            <Tag color="red" className="ml-1" style={{ marginLeft: 8 }}>{unmappedCount}</Tag>
          )}
        </Checkbox>
      </div>
      <Table
        columns={columns}
        dataSource={items}
        rowKey={(r) => `${r.concernKey}-${r.viewpointNumber || 'unmapped'}`}
        loading={isLoading}
        pagination={{ pageSize: 100, showTotal: (total) => `${total} rows` }}
        size="small"
      />
    </div>
  );
}
