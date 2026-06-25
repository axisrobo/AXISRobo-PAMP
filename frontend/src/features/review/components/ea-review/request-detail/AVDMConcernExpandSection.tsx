'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { RequestDetailSection } from './RequestDetailSection';

type ContributionItem = {
  riskCode: string;
  severity: number;
  likelihood: number;
  itemScore: number;
  question: string;
  note: string;
  matchType: string;
};

type ConcernItem = {
  concernKey: string;
  concernName: string;
  layer: string;
  classification: string;
  totalScore: number;
  rationale: string;
  contributions: {
    direct: ContributionItem[];
    tagged: ContributionItem[];
    rules: ContributionItem[];
  };
};

const classificationColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

function flattenContributions(contributions: ConcernItem['contributions']): ContributionItem[] {
  return [
    ...(contributions.direct || []),
    ...(contributions.tagged || []),
    ...(contributions.rules || []),
  ];
}

export function AVDMConcernExpandSection({
  concerns,
  loading,
}: {
  concerns: ConcernItem[];
  loading: boolean;
}) {
  const outerColumns: ColumnsType<ConcernItem> = [
    { title: 'Concern', dataIndex: 'concernKey', key: 'concernKey', width: 100, render: (v: string) => <strong>{v}</strong> },
    { title: 'Concern Name', dataIndex: 'concernName', key: 'concernName', width: 240 },
    { title: 'Layer', dataIndex: 'layer', key: 'layer', width: 180 },
    {
      title: 'Classification', dataIndex: 'classification', key: 'classification', width: 130,
      render: (v: string) => <Tag color={classificationColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Total Score', dataIndex: 'totalScore', key: 'totalScore', width: 100,
      render: (v: number) => v.toFixed(3),
    },
  ];

  const innerColumns: ColumnsType<ContributionItem> = [
    { title: 'Risk Code', dataIndex: 'riskCode', key: 'riskCode', width: 100 },
    { title: 'Severity', dataIndex: 'severity', key: 'severity', width: 80 },
    { title: 'Likelihood', dataIndex: 'likelihood', key: 'likelihood', width: 90 },
    {
      title: 'Item Score', dataIndex: 'itemScore', key: 'itemScore', width: 90,
      render: (v: number) => v.toFixed(4),
    },
    { title: 'Question', dataIndex: 'question', key: 'question', ellipsis: true },
    { title: 'Note', dataIndex: 'note', key: 'note', ellipsis: true },
    {
      title: 'Type', dataIndex: 'matchType', key: 'matchType', width: 80,
      render: (v: string) => <Tag>{v}</Tag>,
    },
  ];

  const summary = {
    mandatory: concerns.filter(c => c.classification === 'Mandatory').length,
    recommended: concerns.filter(c => c.classification === 'Recommended').length,
    optional: concerns.filter(c => c.classification === 'Optional').length,
  };

  return (
    <RequestDetailSection title="Architecture Concerns" defaultOpen>
      <div className="mb-3 flex gap-3 text-xs">
        <Tag color="red">Mandatory: {summary.mandatory}</Tag>
        <Tag color="gold">Recommended: {summary.recommended}</Tag>
        <Tag>Optional: {summary.optional}</Tag>
      </div>
      <Table
        columns={outerColumns}
        dataSource={concerns}
        rowKey="concernKey"
        loading={loading}
        expandable={{
          expandedRowRender: (record) => {
            const items = flattenContributions(record.contributions);
            if (items.length === 0) return <div className="text-xs text-text-secondary px-4 py-2">No questionnaire item contributions</div>;
            return (
              <Table
                columns={innerColumns}
                dataSource={items}
                rowKey={(r, i) => `${record.concernKey}-${r.riskCode}-${i}`}
                pagination={{ pageSize: 10, showSizeChanger: false }}
                size="small"
              />
            );
          },
          rowExpandable: (record) => flattenContributions(record.contributions).length > 0,
        }}
        pagination={false}
        size="small"
      />
    </RequestDetailSection>
  );
}
