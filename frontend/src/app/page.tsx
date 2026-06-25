'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { HomeLayout } from '@/shared/components/layout/HomeLayout';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';

export default function RequesterPage() {
  const { user, loading: authLoading } = useAuth();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const isAdmin = user?.roles?.includes('ea_admin') ?? false;
  const isReviewer = user?.roles?.includes('ea_reviewer') ?? false;

  const { data, isLoading } = useQuery({
    queryKey: ['requesterRequests', user?.id, page, pageSize],
    queryFn: () => {
      const params: Record<string, any> = {
        page,
        pageSize,
        sortBy: 'createdAt',
        sortOrder: 'desc',
      };
      if (!isAdmin && !isReviewer) {
        params.requestorName = user?.id;
      }
      return api.get<any>('/ea-requests', params);
    },
    enabled: !authLoading && !!user?.id,
  });

  const columns: Column<any>[] = [
    {
      key: 'requestId',
      title: 'Request ID',
      pinned: 'left',
      render: (value, record) => {
        const href = record.status === 'Draft'
          ? `/ea-review/request/create?id=${record.id}`
          : `/request/${record.requestId || value}`;

        return (
          <Link href={href} className="text-primary-blue hover:underline font-medium">
            {value || record.requestId}
          </Link>
        );
      },
    },
    {
      key: 'status',
      title: 'Status',
      render: (value) => <StatusBadge status={value} />,
    },
    { key: 'projectId', title: 'Project ID' },
    { key: 'projectName', title: 'Project Name' },
    {
      key: 'changedAt',
      title: 'Last Updated',
      render: (value, record) => {
        const timestamp = value || record.createdAt;
        return timestamp
          ? new Date(timestamp).toLocaleString('en-CA', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false,
            }).replace(',', '')
          : '-';
      },
    },
  ];

  return (
    <HomeLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <section className="rounded-card bg-mdb-teal-deep p-8 shadow-mockup -mx-4 md:mx-0">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-3">
              <span className="inline-block rounded-pill bg-mdb-green/20 text-mdb-green text-xs font-semibold px-3 py-1">Architecture Governance Platform</span>
              <h1 className="text-3xl md:text-4xl font-medium text-white leading-tight">Request Creation And Architecture Check</h1>
              <p className="max-w-2xl text-base text-mdb-stone leading-relaxed">
                Create EA review requests, upload architecture diagrams, and run AI-powered architecture detection. Draft requests reopen the creation flow. Submitted requests open the architecture check detail view.
              </p>
            </div>
            <Link href="/ea-review/request/create" className="btn-primary whitespace-nowrap">Create Request</Link>
          </div>
        </section>

        <section className="card-default">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-mdb-ink">{isAdmin || isReviewer ? 'All Requests' : 'My Requests'}</h2>
              <p className="text-sm text-mdb-steel">Continue drafts or open submitted requests to review AI detection results.</p>
            </div>
            <Link href="/ea-review/request/create" className="btn-link">New Request</Link>
          </div>

          <DataTable
            columns={columns}
            data={data?.data ?? []}
            rowKey="id"
            loading={isLoading}
          />

          {data && (
            <Pagination
              currentPage={page}
              totalPages={data.totalPages || 1}
              totalItems={data.total || 0}
              pageSize={pageSize}
              onPageChange={setPage}
              onPageSizeChange={(size) => {
                setPageSize(size);
                setPage(1);
              }}
            />
          )}
        </section>

        <section className="card-default mt-6">
          <h2 className="text-lg font-semibold text-mdb-ink mb-3">References</h2>
          <div className="space-y-3 text-sm text-mdb-slate">
            <div className="leading-relaxed">
              <span className="font-medium text-mdb-ink">[1]</span> Han, H. <a href="https://doi.org/10.20944/preprints202601.0720.v1" target="_blank" rel="noopener noreferrer" className="text-mdb-green-dark hover:underline">PACT: A Reference Viewpoint Taxonomy for Software-Intensive Systems</a>. <em>Preprints</em> 2026, 2026010720.
            </div>
            <div className="leading-relaxed">
              <span className="font-medium text-text-primary">[2]</span> Han, H. <a href="https://doi.org/10.36227/techrxiv.176948759.92525674/v1" target="_blank" rel="noopener noreferrer" className="text-primary-blue hover:underline">AVDM: A Risk-Informed Decision Model for Architecture Viewpoint Selection</a>. <em>TechRxiv</em>, 27 January 2026.
            </div>
            <div className="leading-relaxed">
              <span className="font-medium text-text-primary">[3]</span> Han, H. <a href="https://doi.org/10.36227/techrxiv.176948904.46258539/v1" target="_blank" rel="noopener noreferrer" className="text-primary-blue hover:underline">AADM: An Architecture Artifact Decision Model for Risk-Aware Documentation Scope</a>. <em>TechRxiv</em>, 27 January 2026.
            </div>
            <div className="leading-relaxed">
              <span className="font-medium text-text-primary">[4]</span> Han, H. <a href="https://doi.org/10.36227/techrxiv.176948938.83267225/v1" target="_blank" rel="noopener noreferrer" className="text-primary-blue hover:underline">ARCM: Responsibility Configuration in Multi-View Architecture Descriptions</a>. <em>TechRxiv</em>, 27 January 2026.
            </div>
          </div>
        </section>
      </div>
    </HomeLayout>
  );
}