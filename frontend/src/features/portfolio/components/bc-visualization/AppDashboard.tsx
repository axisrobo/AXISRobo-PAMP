'use client';

import { useMemo, useState } from 'react';
import type { Application, CapNode } from './types';
import { getDomainPalette } from './constants';
import { MultiSelect } from '@/shared/components/ui/MultiSelect';

interface AppDashboardProps {
  applications: ReadonlyArray<Application>;
  capabilities: ReadonlyArray<CapNode>;
}

function KpiCard({ label, value, colorClass = 'text-gray-900' }: { label: string; value: string | number; colorClass?: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold tracking-tight ${colorClass}`}>{value}</p>
    </div>
  );
}

export function AppDashboard({ applications, capabilities }: AppDashboardProps) {
  const [search, setSearch] = useState('');
  const [statusFilters, setStatusFilters] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<'default' | 'tco-desc' | 'tco-asc'>('default');

  // Build capability lookup: bcId → CapNode (for tooltip descriptions)
  const capLookup = useMemo(() => {
    const map = new Map<string, CapNode>();
    for (const cap of capabilities) {
      map.set(cap.id, cap);
    }
    return map;
  }, [capabilities]);

  const statusOptions = useMemo(
    () => Array.from(new Set(applications.map((a) => a.appStatus).filter(Boolean))).map((s) => ({ label: s, value: s })),
    [applications],
  );

  const filtered = useMemo(() => {
    let list = [...applications];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (a) =>
          a.appName.toLowerCase().includes(q) ||
          a.appSolutionOwner.toLowerCase().includes(q),
      );
    }
    if (statusFilters.length > 0) {
      list = list.filter((a) => statusFilters.includes(a.appStatus));
    }
    if (sortBy === 'tco-desc') {
      list.sort((a, b) => (b.actualK ?? -1) - (a.actualK ?? -1));
    } else if (sortBy === 'tco-asc') {
      list.sort((a, b) => (a.actualK ?? Infinity) - (b.actualK ?? Infinity));
    }
    return list;
  }, [applications, search, statusFilters, sortBy]);

  const activeCount = applications.filter((a) => a.appStatus === 'Active').length;
  const plannedCount = applications.filter((a) => a.appStatus === 'Planned').length;
  const totalMappings = applications.reduce((sum, a) => sum + a.capabilities.length, 0);
  const totalTco = applications.reduce((sum, a) => sum + (a.actualK ?? 0), 0);
  const tcoLabel = totalTco >= 1000
    ? `$${(totalTco / 1000).toFixed(1)}M`
    : `$${Math.round(totalTco)}K`;

  return (
    <div className="flex flex-col gap-4">
      {/* KPI Row */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCard label="Total Applications" value={applications.length} />
        <KpiCard label="Active" value={activeCount} colorClass="text-emerald-600" />
        <KpiCard label="Planned" value={plannedCount} colorClass="text-sky-600" />
        <KpiCard label="Total Mappings" value={totalMappings} colorClass="text-violet-600" />
        {/* <KpiCard label="Total Actual TCO" value={tcoLabel} colorClass="text-amber-600" /> */}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search applications..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded px-3 py-2 text-sm w-48 min-w-0 focus:outline-none focus:border-primary-blue"
        />
        <MultiSelect
          options={statusOptions}
          value={statusFilters}
          onChange={setStatusFilters}
          placeholder="All Statuses"
          maxDisplay={2}
        />
        <span className="text-xs text-gray-500 whitespace-nowrap">
          {filtered.length} of {applications.length}
        </span>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'default' | 'tco-desc' | 'tco-asc')}
          className="ml-auto border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-primary-blue whitespace-nowrap"
        >
          <option value="default">Sort: Default</option>
          <option value="tco-desc">TCO High → Low</option>
          <option value="tco-asc">TCO Low → High</option>
        </select>
      </div>

      {/* App cards */}
      <div className="grid gap-3">
        {filtered.map((app) => (
          <div key={app.appId} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 className="text-sm font-semibold text-gray-900">
                  {app.appName}
                  {app.appFullName && app.appFullName !== app.appName && (
                    <span className="ml-1.5 font-normal text-gray-400">({app.appFullName})</span>
                  )}
                </h3>
                <p className="text-xs text-gray-500">
                  {app.appId}
                  {app.appOwnerTower && <> &middot; {app.appOwnerTower}</>}
                  {app.appItOwner && <> &middot; IT: {app.appItOwner}</>}
                  {app.ownedBy && <> &middot; Owner: {app.ownedBy}</>}
                </p>
                {app.appDescription && (
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{app.appDescription}</p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  app.appStatus === 'Active'
                    ? 'bg-emerald-50 text-emerald-700'
                    : app.appStatus === 'Planned'
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-amber-50 text-amber-700'
                }`}>
                  {app.appStatus}
                </span>
                {app.geo && (
                  <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium bg-purple-50 text-purple-700">
                    {app.geo}
                  </span>
                )}
                {app.portfolioMgt && (
                  <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium bg-orange-50 text-orange-700">
                    {app.portfolioMgt}
                  </span>
                )}
                {app.bizFunction && (
                  <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium bg-cyan-50 text-cyan-700">
                    {app.bizFunction}
                  </span>
                )}
                {app.actualK != null && (
                  <span className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-50 text-amber-700">
                    TCO: ${app.actualK >= 1000 ? `${(app.actualK / 1000).toFixed(1)}M` : `${Math.round(app.actualK)}K`}
                  </span>
                )}
              </div>
            </div>

            {app.capabilities.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {app.capabilities.map((cap) => {
                  const capNode = capLookup.get(cap.bcId);
                  const tooltipLines = [
                    cap.bcName,
                    capNode?.nameCn ? `(${capNode.nameCn})` : '',
                    `Domain: ${cap.lv1Domain}`,
                    cap.lv2SubDomain ? `Sub-Domain: ${cap.lv2SubDomain}` : '',
                    cap.lv3CapGroup ? `Capability Group: ${cap.lv3CapGroup}` : '',
                    capNode?.description ? `\nDescription: ${capNode.description}` : '',
                    capNode ? `Applications: ${capNode.appCount}` : '',
                  ].filter(Boolean).join('\n');

                  return (
                    <span
                      key={cap.bcId}
                      className="inline-block rounded-md px-2 py-1 text-xs"
                      style={{
                        backgroundColor: getDomainPalette(cap.lv1Domain).fill,
                        color: getDomainPalette(cap.lv1Domain).stroke,
                        border: `1px solid ${getDomainPalette(cap.lv1Domain).stroke}30`,
                      }}
                      title={tooltipLines}
                    >
                      {cap.bcName}
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
