'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Alert, Button, Card, Skeleton, Tag, Typography } from 'antd';
import { ArrowLeft, BookOpen } from 'lucide-react';

import { api } from '@/shared/lib/api';
import {
  ProjectTypeArtifactStatus,
  ProjectTypeGuide,
  ProjectTypeProfile,
  mergeQuestionnaireConfig,
} from '@/features/review/config/questionnaireConfig';

type QuestionnaireConfigResponse = {
  config: Record<string, unknown>;
  source: 'db' | 'default';
};

function projectTypeStatusColor(status: ProjectTypeArtifactStatus) {
  switch (status) {
    case 'Mandatory':
      return 'red';
    case 'Recommended':
      return 'blue';
    case 'Optional':
      return 'gold';
    default:
      return 'default';
  }
}

function GuideSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <Typography.Title level={5} style={{ marginTop: 0 }}>{title}</Typography.Title>
      {children}
    </section>
  );
}

function renderGuide(guide: ProjectTypeGuide, profiles: ProjectTypeProfile[]) {
  return (
    <div className="space-y-5">
      {guide.introduction.length > 0 && (
        <GuideSection title="Overview">
          <div className="space-y-2 text-sm text-slate-600">
            {guide.introduction.map((item) => <p key={item}>{item}</p>)}
          </div>
        </GuideSection>
      )}

      {guide.objectives.length > 0 && (
        <GuideSection title="Objectives">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {guide.objectives.map((item) => (
              <div key={item.title} className="rounded border border-slate-200 p-3">
                <div className="font-medium text-slate-800">{item.title}</div>
                <div className="mt-1 text-sm text-slate-600">{item.description}</div>
              </div>
            ))}
          </div>
        </GuideSection>
      )}

      {(guide.scopeIntro || guide.scopeProjectTypes.length > 0 || guide.scopeNote) && (
        <GuideSection title="Scope">
          <div className="space-y-2 text-sm text-slate-600">
            {guide.scopeIntro && <p>{guide.scopeIntro}</p>}
            {guide.scopeProjectTypes.length > 0 && (
              <ul className="list-disc pl-5">
                {guide.scopeProjectTypes.map((item) => <li key={item}>{item}</li>)}
              </ul>
            )}
            {guide.scopeNote && <p>{guide.scopeNote}</p>}
          </div>
        </GuideSection>
      )}

      {guide.corePrinciples.length > 0 && (
        <GuideSection title="Core Principles">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {guide.corePrinciples.map((item) => (
              <div key={item.title} className="rounded border border-slate-200 p-3">
                <div className="font-medium text-slate-800">{item.title}</div>
                <div className="mt-1 text-sm text-slate-600">{item.description}</div>
              </div>
            ))}
          </div>
        </GuideSection>
      )}

      {guide.governanceBoundary.length > 0 && (
        <GuideSection title="EA Governance Boundary">
          <ul className="list-disc pl-5 text-sm text-slate-600">
            {guide.governanceBoundary.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </GuideSection>
      )}

      {guide.recommendedUsage.length > 0 && (
        <GuideSection title="Recommended Usage">
          <ul className="list-disc pl-5 text-sm text-slate-600">
            {guide.recommendedUsage.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </GuideSection>
      )}

      {(guide.artifactSelectionIntro.length > 0 || profiles.length > 0) && (
        <GuideSection title="Architecture Artifact Selection">
          <div className="space-y-2 text-sm text-slate-600">
            {guide.artifactSelectionIntro.map((item) => <p key={item}>{item}</p>)}
          </div>
          {profiles.length > 0 && (
            <div className="mt-4 overflow-x-auto rounded border border-slate-200">
              <table className="min-w-full border-collapse text-sm">
                <thead className="bg-slate-50 text-slate-700">
                  <tr>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Project Type</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Description</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Artifact Baseline</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Typical Patterns</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Typical Risks</th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.map((profile) => (
                    <tr key={profile.value}>
                      <td className="border-b border-slate-100 px-3 py-2 align-top font-medium text-slate-800">{profile.label}</td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">{profile.description}</td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top">
                        <div className="flex flex-wrap gap-1">
                          {profile.artifactSelections.map((selection) => (
                            <Tag key={`${profile.value}-${selection.artifactKey}`} color={projectTypeStatusColor(selection.status)}>
                              {selection.artifactLabel}: {selection.status}
                            </Tag>
                          ))}
                        </div>
                      </td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">
                        {profile.typicalPatterns.length > 0 ? profile.typicalPatterns.join(', ') : '-'}
                      </td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">
                        {profile.typicalRisks.length > 0 ? profile.typicalRisks.join(', ') : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GuideSection>
      )}

      {guide.legend.length > 0 && (
        <GuideSection title="Legend">
          <div className="flex flex-wrap gap-2">
            {guide.legend.map((item) => <Tag key={item.symbol}>{item.symbol}: {item.meaning}</Tag>)}
          </div>
        </GuideSection>
      )}

      {guide.note && <Alert type="info" showIcon message={guide.note} />}
    </div>
  );
}

export default function ProjectTypeGuidePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['avdmQuestionnaireConfig', 'default', 'projectTypeGuidePage'],
    queryFn: () => api.get<QuestionnaireConfigResponse>('/avdm/questionnaire-config', { configKey: 'default' }),
  });
  const config = mergeQuestionnaireConfig(data?.config || {});

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary-blue">
              <BookOpen className="h-4 w-4" />
              AVDM Guide
            </div>
            <Typography.Title level={2} style={{ margin: 0 }}>
              {config.projectTypeGuide.title || 'Project Type - Architecture Artifact Matrix'}
            </Typography.Title>
            <Typography.Paragraph className="mt-3 max-w-3xl text-slate-600">
              Use this reference to understand project-type-driven architecture artifact baselines. The request form links here instead of embedding the full matrix in the questionnaire flow.
            </Typography.Paragraph>
          </div>
          <Link href="/ea-review/request/create">
            <Button icon={<ArrowLeft className="h-4 w-4" />}>Back to Request Form</Button>
          </Link>
        </div>
      </section>

      {isLoading ? (
        <Card>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      ) : renderGuide(config.projectTypeGuide, config.projectTypeProfiles)}
    </div>
  );
}
