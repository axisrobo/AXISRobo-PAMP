'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';

import { RequestDetailSection } from './RequestDetailSection';

type ViewpointConcern = {
  concernKey: string;
  concernName: string;
  classification: string;
  totalScore: number;
};

type ViewpointItem = {
  viewpointId: string;
  viewpointNumber: number;
  viewpointName: string;
  layerName: string;
  classification: string;
  totalScore: number;
  concerns: ViewpointConcern[];
  artifacts: string[];
};

const classificationColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

export function AVDMViewpointExpandSection({
  viewpoints,
  loading,
}: {
  viewpoints: ViewpointItem[];
  loading: boolean;
}) {
  const columns: ColumnsType<ViewpointItem> = [
    {
      title: 'Viewpoint',
      dataIndex: 'viewpointName',
      key: 'viewpointName',
      width: 280,
      render: (value: string, record) => <strong>{record.viewpointNumber}. {value}</strong>,
    },
    { title: 'Layer', dataIndex: 'layerName', key: 'layerName', width: 200 },
    {
      title: 'Classification',
      dataIndex: 'classification',
      key: 'classification',
      width: 130,
      render: (value: string) => <Tag color={classificationColor[value] || 'default'}>{value}</Tag>,
    },
    {
      title: 'Score',
      dataIndex: 'totalScore',
      key: 'totalScore',
      width: 90,
      render: (value: number) => value.toFixed(3),
    },
    {
      title: 'Artifacts',
      dataIndex: 'artifacts',
      key: 'artifacts',
      render: (artifacts: string[]) => (
        <div className="flex flex-wrap gap-1">
          {artifacts.length > 0 ? artifacts.map((artifact) => <Tag key={artifact}>{artifact}</Tag>) : <span className="text-text-secondary">No mapped artifact</span>}
        </div>
      ),
    },
  ];

  const concernColumns: ColumnsType<ViewpointConcern> = [
    { title: 'Concern', dataIndex: 'concernKey', key: 'concernKey', width: 120, render: (value: string) => <strong>{value}</strong> },
    { title: 'Concern Name', dataIndex: 'concernName', key: 'concernName' },
    {
      title: 'Classification',
      dataIndex: 'classification',
      key: 'classification',
      width: 130,
      render: (value: string) => <Tag color={classificationColor[value] || 'default'}>{value}</Tag>,
    },
    { title: 'Score', dataIndex: 'totalScore', key: 'totalScore', width: 90, render: (value: number) => value.toFixed(3) },
  ];

  return (
    <RequestDetailSection title="Architecture Viewpoints" defaultOpen>
      <Table
        columns={columns}
        dataSource={viewpoints}
        rowKey="viewpointId"
        loading={loading}
        expandable={{
          expandedRowRender: (record) => (
            <Table
              columns={concernColumns}
              dataSource={record.concerns}
              rowKey={(item) => `${record.viewpointId}-${item.concernKey}`}
              pagination={false}
              size="small"
            />
          ),
          rowExpandable: (record) => record.concerns.length > 0,
        }}
        pagination={false}
        size="small"
      />
    </RequestDetailSection>
  );
}
