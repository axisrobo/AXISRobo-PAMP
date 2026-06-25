'use client';

import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { RequestDetailSection } from './RequestDetailSection';

type ConcernContribution = {
  direct: Array<{ riskCode: string; itemScore: number }>;
  tagged: Array<{ riskCode: string; itemScore: number }>;
  rules: Array<{ riskCode: string; score: number }>;
};

type ArtifactItem = {
  artifactId: string;
  artifactName: string;
  associatedConcernKey: string;
  associatedConcernName: string;
  classification: string;
  totalScore: number;
  status: string;
  contributions: ConcernContribution;
};

type ScoreBreakdown = {
  concernKey: string;
  directScore: number;
  taggedScore: number;
  ruleScore: number;
  finalScore: number;
};

const classificationColor: Record<string, string> = {
  Mandatory: 'red',
  Recommended: 'gold',
  Optional: 'default',
};

export function AVDMArtifactExpandSection({
  artifacts,
  loading,
}: {
  artifacts: ArtifactItem[];
  loading: boolean;
}) {
  const outerColumns: ColumnsType<ArtifactItem> = [
    { title: 'Artifact', dataIndex: 'artifactName', key: 'artifactName', width: 280, render: (v: string) => <strong>{v}</strong> },
    {
      title: 'Concern', dataIndex: 'associatedConcernName', key: 'associatedConcernName', width: 240,
      render: (v: string, r: ArtifactItem) => <span>{r.associatedConcernKey}: {v}</span>,
    },
    {
      title: 'Classification', dataIndex: 'classification', key: 'classification', width: 130,
      render: (v: string) => <Tag color={classificationColor[v] || 'default'}>{v}</Tag>,
    },
    {
      title: 'Total Score', dataIndex: 'totalScore', key: 'totalScore', width: 100,
      render: (v: number) => v.toFixed(3),
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (v: string) => <Tag color={v === 'selected' ? 'blue' : 'default'}>{v}</Tag>,
    },
  ];

  const innerColumns: ColumnsType<ScoreBreakdown> = [
    { title: 'Concern', dataIndex: 'concernKey', key: 'concernKey', width: 100 },
    { title: 'Direct Score', dataIndex: 'directScore', key: 'directScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Tag Score', dataIndex: 'taggedScore', key: 'taggedScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Rule Score', dataIndex: 'ruleScore', key: 'ruleScore', width: 100, render: (v: number) => v.toFixed(4) },
    { title: 'Final Score', dataIndex: 'finalScore', key: 'finalScore', width: 100, render: (v: number) => v.toFixed(3) },
  ];

  function buildBreakdown(record: ArtifactItem): ScoreBreakdown[] {
    const contrib = record.contributions;
    const directScore = (contrib.direct || []).reduce((s, i) => s + (i.itemScore || 0), 0);
    const taggedScore = (contrib.tagged || []).reduce((s, i) => s + (i.itemScore || 0), 0);
    const ruleScore = (contrib.rules || []).reduce((s, i) => s + (i.score || 0), 0);

    return [{
      concernKey: record.associatedConcernKey,
      directScore,
      taggedScore,
      ruleScore,
      finalScore: record.totalScore,
    }];
  }

  return (
    <RequestDetailSection title="Architecture Artifacts" defaultOpen>
      <Table
        columns={outerColumns}
        dataSource={artifacts}
        rowKey="artifactId"
        loading={loading}
        expandable={{
          expandedRowRender: (record) => (
            <Table
              columns={innerColumns}
              dataSource={buildBreakdown(record)}
              rowKey="concernKey"
              pagination={false}
              size="small"
            />
          ),
        }}
        pagination={false}
        size="small"
      />
    </RequestDetailSection>
  );
}
