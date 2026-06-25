import { appConfig } from '@/shared/lib/app-config';

const clusters = [
  { id: 'C1', name: 'Foundations and Epistemology' },
  { id: 'C2', name: 'PACT - Agent Architecture and Engineering', active: true },
  { id: 'C3', name: 'Knowledge and Memory Systems' },
  { id: 'C4', name: 'Reasoning and Decision Theory' },
  { id: 'C5', name: 'Safety, Alignment, and Governance' },
  { id: 'C6', name: 'Human-AI Collaboration and UX' },
  { id: 'C7', name: 'Domain Intelligence and Vertical AI' },
  { id: 'C8', name: 'Infrastructure and Runtime Platforms' },
  { id: 'C9', name: 'Evaluation, Benchmarks, and Metrics' },
  { id: 'C10', name: 'Industrialization and Operations' },
  { id: 'C11', name: 'Societal Systems and Civilization Impact' },
];

const programs = [
  'Program 01: Agent Workflow Engineering',
  'Program 02: Multi-Agent Coordination',
  'Program 03: Architecture Review Automation',
  'Program 04: Concern-Driven Decisioning',
  'Program 05: Artifact Requirement Intelligence',
  'Program 06: Review and Governance Pipeline',
];

export default function AICTClusterMapPage() {
  return (
    <div className="p-6 space-y-6">
      <section className="rounded-lg border border-border-light bg-white p-6">
        <div className="text-xs font-semibold text-brand-primary uppercase tracking-wide">AICT System Map</div>
        <h1 className="mt-2 text-2xl font-semibold text-text-primary">{appConfig.appTitle}</h1>
        <p className="mt-2 text-sm text-text-secondary">{appConfig.appSubtitle}</p>
        <p className="mt-3 text-sm text-text-secondary">
          AICT is a long-horizon research cluster composed of 1000+ papers, 11 clusters, and 20+ programs.
          This page highlights the current product focus in Cluster 2 (PACT).
        </p>
      </section>

      <section className="rounded-lg border border-border-light bg-white p-6">
        <h2 className="text-lg font-semibold text-text-primary">Cluster Landscape (11)</h2>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {clusters.map((cluster) => (
            <div
              key={cluster.id}
              className={`rounded-md border p-3 ${
                cluster.active
                  ? 'border-brand-primary/40 bg-brand-primary/10'
                  : 'border-border-light bg-gray-50'
              }`}
            >
              <div className={`text-xs font-semibold ${cluster.active ? 'text-brand-primary' : 'text-text-secondary'}`}>
                {cluster.id}
              </div>
              <div className="mt-1 text-sm font-medium text-text-primary">{cluster.name}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-border-light bg-white p-6">
        <h2 className="text-lg font-semibold text-text-primary">Cluster 2 Programs (Sample)</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Current implementation scope in this product aligns with PACT and AVDM preparation workflows.
        </p>
        <ul className="mt-4 space-y-2">
          {programs.map((program) => (
            <li key={program} className="rounded-md border border-border-light px-3 py-2 text-sm text-text-primary bg-gray-50">
              {program}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
