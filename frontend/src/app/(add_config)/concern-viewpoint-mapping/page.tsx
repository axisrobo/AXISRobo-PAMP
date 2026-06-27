'use client';

import { useQuery } from '@tanstack/react-query';
import { Table, Tag, Typography, Checkbox, Select } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useState, useMemo } from 'react';
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
  const [concernLayerFilter, setConcernLayerFilter] = useState<string | undefined>();
  const [viewpointLayerFilter, setViewpointLayerFilter] = useState<string | undefined>();

  const { data, isLoading } = useQuery({
    queryKey: ['concernViewpointMapping', includeUnmapped],
    queryFn: () => api.get<{ data: MappingItem[]; total: number }>('/avdm/concern-viewpoint-mapping', { includeUnmapped }),
  });

  const items = data?.data ?? [];
  const unmappedCount = includeUnmapped ? items.filter((i) => !i.viewpointName).length : 0;

  const concernLayerOptions = useMemo(() =>
    [...new Set(items.map((i) => i.concernLayer).filter(Boolean))]
      .sort()
      .map((l) => ({ label: l, value: l })),
    [items],
  );
  const viewpointLayerOptions = useMemo(() =>
    [...new Set(items.map((i) => i.viewpointLayer).filter(Boolean))]
      .sort()
      .map((l) => ({ label: l, value: l })),
    [items],
  );

  const filteredItems = useMemo(() =>
    items.filter((i) =>
      (!concernLayerFilter || i.concernLayer === concernLayerFilter) &&
      (!viewpointLayerFilter || i.viewpointLayer === viewpointLayerFilter),
    ),
    [items, concernLayerFilter, viewpointLayerFilter],
  );

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
          Show only unmapped
          {includeUnmapped && unmappedCount > 0 && (
            <Tag color="red" style={{ marginLeft: 8 }}>{unmappedCount}</Tag>
          )}
        </Checkbox>
      </div>
      <div className="flex gap-3 flex-wrap">
        <Select
          allowClear
          placeholder="All Concern Layers"
          style={{ width: 260 }}
          value={concernLayerFilter}
          onChange={(v) => setConcernLayerFilter(v)}
          options={concernLayerOptions}
        />
        <Select
          allowClear
          placeholder="All Viewpoint Layers"
          style={{ width: 260 }}
          value={viewpointLayerFilter}
          onChange={(v) => setViewpointLayerFilter(v)}
          options={viewpointLayerOptions}
        />
      </div>
      <Table
        columns={columns}
        dataSource={filteredItems}
        rowKey={(r) => `${r.concernKey}-${r.viewpointNumber || 'unmapped'}`}
        loading={isLoading}
        pagination={{ pageSize: 100, showTotal: (total) => `${total} rows` }}
        size="small"
      />
    </div>
  );
}
