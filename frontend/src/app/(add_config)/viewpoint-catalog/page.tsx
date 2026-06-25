'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, Tag, Typography, Checkbox } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useState } from 'react';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

type ViewpointItem = {
  id: string;
  viewpointNumber: number;
  layerName: string;
  viewpointName: string;
  logicalPhysical: string;
  structureBehavior: string;
  purpose: string;
  example: string;
  primarySource: string;
  audience: string;
  notes: string;
  sortOrder: number;
  isActive: boolean;
};

export default function ViewpointCatalogPage() {
  const [showInactive, setShowInactive] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['viewpointCatalog'],
    queryFn: () => api.get<{ data: ViewpointItem[]; total: number }>('/avdm/viewpoints'),
  });

  const items = (data?.data ?? []).filter((v) => showInactive || v.isActive);

  const columns: ColumnsType<ViewpointItem> = [
    { title: '#', dataIndex: 'viewpointNumber', width: 50 },
    { title: 'Viewpoint Name', dataIndex: 'viewpointName', width: 280, render: (v: string) => <strong>{v}</strong> },
    { title: 'Layer', dataIndex: 'layerName', width: 180, render: (v: string) => <Tag>{v}</Tag> },
    { title: 'L/P', dataIndex: 'logicalPhysical', width: 50 },
    { title: 'S/B', dataIndex: 'structureBehavior', width: 50 },
    { title: 'Purpose', dataIndex: 'purpose', ellipsis: true, width: 300 },
    { title: 'Primary Source', dataIndex: 'primarySource', width: 160 },
    { title: 'Audience', dataIndex: 'audience', width: 140 },
    { title: 'Active', dataIndex: 'isActive', width: 70, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Yes' : 'No'}</Tag> },
  ];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>Viewpoint Catalog</Title>
          <p className="text-sm text-text-secondary">Architecture viewpoints (PACT framework)</p>
        </div>
        <Checkbox checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)}>Show inactive</Checkbox>
      </div>
      <Table
        columns={columns}
        dataSource={items}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 100, showTotal: (total) => `${total} viewpoints` }}
        size="small"
        expandable={{
          expandedRowRender: (record) => (
            <div className="space-y-2 px-2 py-1 text-sm">
              {record.purpose && <div><strong>Purpose:</strong> {record.purpose}</div>}
              {record.example && <div><strong>Example:</strong> {record.example}</div>}
              {record.notes && <div><strong>Notes:</strong> {record.notes}</div>}
            </div>
          ),
        }}
      />
    </div>
  );
}
