'use client';

import Link from 'next/link';
import { Alert } from 'antd';
import { ClipboardList, FileJson, GitBranch, Layers3, Network, ShieldCheck } from 'lucide-react';

import { PageLayout } from '@/shared/components/layout/PageLayout';
import { useAuth } from '@/shared/lib/auth-context';

const adminItems = [
  {
    title: 'Questionnaire Config',
    description: 'Maintain question categories, question text, range options, and design intent without concern scoring rules.',
    href: '/questionnaire-config',
    icon: ClipboardList,
    action: 'Open Config',
  },
  {
    title: 'Questionnaire & Concern Mapping',
    description: 'Maintain answer-to-concern mappings, combination rules, and additive concern risk scores.',
    href: '/concern-mapping-config',
    icon: GitBranch,
    action: 'Tune Mapping',
  },
  {
    title: 'Architecture Artifact Catalog',
    description: 'Maintain preparation-stage diagram and artifact definitions, including purpose, typical contents, and supported viewpoints.',
    href: '/architecture-artifact-catalog',
    icon: Layers3,
    action: 'Manage Artifacts',
  },
  {
    title: 'Viewpoint Catalog',
    description: 'Browse the 45 architecture viewpoints organized by PACT layers with logical/physical and structure/behavior dimensions.',
    href: '/viewpoint-catalog',
    icon: Network,
    action: 'Browse Viewpoints',
  },
  {
    title: 'Concern & Viewpoint Mapping',
    description: 'Map each architecture concern to the viewpoints that address it, forming the middle layer of the Questionnaire→Concern→Viewpoint→Artifact chain.',
    href: '/concern-viewpoint-mapping',
    icon: GitBranch,
    action: 'View Mappings',
  },
  {
    title: 'Viewpoint & Artifact Mapping',
    description: 'Manage the canonical mapping matrix between architecture viewpoints and artifact types, including L/P and S/B semantics.',
    href: '/viewpoint-artifact-mapping',
    icon: Network,
    action: 'Open Matrix',
  },
  {
    title: 'Concern Catalog',
    description: 'Maintain the 52 architecture concerns and active/inactive status through the AVDM concern master data API.',
    href: '/pact-concern-catalog',
    icon: FileJson,
    action: 'Manage Catalog',
  },
];

export default function AdminWorkspacePage() {
  const { hasRole, loading } = useAuth();
  const isAdmin = hasRole('ea_admin');

  return (
    <PageLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <section className="border-b border-slate-200 bg-white px-6 py-7">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium text-primary-blue">
                <ShieldCheck className="h-4 w-4" />
                Admin Workspace
              </div>
              <h1 className="text-2xl font-semibold text-text-primary">AVDM Governance Setup</h1>
              <p className="max-w-3xl text-sm text-text-secondary">
                Manage the preparation-stage master data that drives questionnaire setup, canonical viewpoint semantics, artifact definitions, concern mapping, and project architecture concern classification.
              </p>
            </div>
          </div>
        </section>

        <div className="px-6 pb-8">
          {!loading && !isAdmin && (
            <Alert type="warning" showIcon message="Only EA Admin can access this workspace." />
          )}

          {isAdmin && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-4">
              {adminItems.map((item) => {
                const Icon = item.icon;
                return (
                  <section key={item.title} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-primary-blue">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="text-base font-semibold text-text-primary">{item.title}</h2>
                    <p className="mt-2 min-h-16 text-sm leading-6 text-text-secondary">{item.description}</p>
                    <Link
                      href={item.href}
                      className="mt-5 inline-flex items-center justify-center rounded-lg bg-primary-blue px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-blue-hover"
                    >
                      {item.action}
                    </Link>
                  </section>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}