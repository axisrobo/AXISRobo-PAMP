'use client';

import { Empty, Skeleton, Tag } from 'antd';

import { DataTable, type Column } from '@/shared/components/ui/DataTable';
import { RequestDetailSection } from '@/features/review/components/ea-review/request-detail/RequestDetailSection';

export type ConcernClassification = 'Mandatory' | 'Recommended' | 'Optional';

export type AVDMConcernDecision = {
  concernKey: string;
  concernName: string;
  layer: string;
  score: number;
  classification: ConcernClassification;
  rationale: string;
};

export type AVDMEvaluation = {
  projectId: string;
  decisions: AVDMConcernDecision[];
  layerSummary?: Array<{
    layer: string;
    mandatory: number;
    recommended: number;
    optional: number;
  }>;
};

const classificationOrder: ConcernClassification[] = ['Mandatory', 'Recommended', 'Optional'];

const classificationPresentation: Record<ConcernClassification, { label: string; color: string }> = {
  Mandatory: { label: 'Mandatory', color: 'red' },
  Recommended: { label: 'Recommended', color: 'gold' },
  Optional: { label: 'Optional', color: 'default' },
};

function sortDecisions(decisions: AVDMConcernDecision[]) {
  const rank = new Map(classificationOrder.map((item, index) => [item, index]));
  return [...decisions].sort((left, right) => {
    const classCompare = (rank.get(left.classification) ?? 99) - (rank.get(right.classification) ?? 99);
    if (classCompare !== 0) return classCompare;
    if (right.score !== left.score) return right.score - left.score;
    return left.concernKey.localeCompare(right.concernKey);
  });
}

function scoreLabel(score: number) {
  return Number.isFinite(score) ? score.toFixed(3) : '-';
}

export function AVDMConcernListSection({
  evaluation,
  loading = false,
}: {
  evaluation?: AVDMEvaluation | null;
  loading?: boolean;
}) {
  const decisions = sortDecisions(evaluation?.decisions ?? []);
  const counts = classificationOrder.reduce<Record<ConcernClassification, number>>((acc, classification) => {
    acc[classification] = decisions.filter((item) => item.classification === classification).length;
    return acc;
  }, { Mandatory: 0, Recommended: 0, Optional: 0 });

  const columns: Column<AVDMConcernDecision>[] = [
    {
      key: 'classification',
      title: 'Priority',
      width: 130,
      render: (_value, record) => {
        const presentation = classificationPresentation[record.classification];
        return <Tag color={presentation.color}>{presentation.label}</Tag>;
      },
    },
    {
      key: 'concernKey',
      title: 'Concern',
      width: 120,
      render: (_value, record) => <span className="font-semibold text-text-primary">{record.concernKey}</span>,
    },
    {
      key: 'concernName',
      title: 'Viewpoint Name',
      width: 260,
    },
    {
      key: 'layer',
      title: 'Layer',
      width: 240,
    },
    {
      key: 'score',
      title: 'Score',
      width: 90,
      render: (_value, record) => scoreLabel(record.score),
    },
    {
      key: 'rationale',
      title: 'Rationale',
      width: 360,
    },
  ];

  return (
    <RequestDetailSection
      title="Architecture Concerns"
      defaultOpen
      actions={
        decisions.length > 0 ? (
          <div className="flex flex-wrap items-center gap-2">
            {classificationOrder.map((classification) => {
              const presentation = classificationPresentation[classification];
              return (
                <Tag key={classification} color={presentation.color}>
                  {presentation.label}: {counts[classification]}
                </Tag>
              );
            })}
          </div>
        ) : null
      }
    >
      {loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : decisions.length > 0 ? (
        <DataTable
          columns={columns}
          data={decisions}
          rowKey="concernKey"
          pagination={{ pageSize: 12, showSizeChanger: false }}
          emptyText="No architecture concerns"
        />
      ) : (
        <div className="py-4">
          <Empty description="No questionnaire evaluation yet" />
        </div>
      )}
    </RequestDetailSection>
  );
}
