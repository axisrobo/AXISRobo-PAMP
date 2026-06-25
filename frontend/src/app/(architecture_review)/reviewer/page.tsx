'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert } from 'antd';

import { PageLayout } from '@/shared/components/layout/PageLayout';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';

const REVIEW_QUEUE_STATUSES = [
  'Submitted',
  'Accepted by EA',
  'In Progress',
  'In Validation',
  'Approved with Actions',
  'Rejected',
  'Returned by EA',
].join(',');

function formatDateTime(value?: string) {
  return value
    ? new Date(value).toLocaleString('en-CA', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      }).replace(',', '')
    : '-';
}

export default function ReviewerPage() {
  const { user, loading: authLoading, hasRole } = useAuth();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const isAdmin = hasRole('ea_admin');
  const isReviewer = hasRole('ea_reviewer');
  const canReview = isAdmin || isReviewer;

  const queryParams = useMemo(
    () => ({
      page,
      pageSize,
      status: REVIEW_QUEUE_STATUSES,
      reviewerName: isAdmin ? undefined : user?.id,
      sortBy: 'updatedAt',
      sortOrder: 'desc',
    }),
    [isAdmin, page, pageSize, user?.id],
  );

  const { data, isLoading } = useQuery({
    queryKey: ['reviewerRequests', user?.id, isAdmin, page, pageSize],
    queryFn: () => api.get<any>('/ea-requests', queryParams),
    enabled: !authLoading && canReview && (isAdmin || !!user?.id),
  });

  const columns: Column<any>[] = [
    {
      key: 'requestId',
      title: 'Request ID',
      pinned: 'left',
      render: (value, record) => (
        <Link href={`/request/${record.requestId || value}`} className="text-primary-blue hover:underline font-medium">
          {value || record.requestId}
        </Link>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      render: (value) => <StatusBadge status={value} />,
    },
    { key: 'projectId', title: 'Project ID' },
    { key: 'projectName', title: 'Project Name' },
    { key: 'requestorName', title: 'Requester' },
    { key: 'reviewerName', title: 'Reviewer' },
    {
      key: 'changedAt',
      title: 'Last Updated',
      render: (value, record) => formatDateTime(value || record.createdAt),
    },
  ];

  return (
    <PageLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-primary-blue">Reviewer Workspace</p>
              <h1 className="text-2xl font-semibold text-text-primary">Architecture Review Queue</h1>
              <p className="max-w-2xl text-sm text-text-secondary">
                Open a submitted request to review the questionnaire-derived architecture concerns, priorities, and AVDM stage confirmations.
              </p>
            </div>
          </div>
        </section>

        {!authLoading && !canReview && (
          <Alert type="warning" showIcon message="You do not have reviewer permission for this workspace." />
        )}

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">Review Requests</h2>
              <p className="text-sm text-text-secondary">
                {isAdmin ? 'EA admins can see the review queue across reviewers.' : 'Requests assigned to you for architecture review.'}
              </p>
            </div>
          </div>

          <DataTable
            columns={columns}
            data={data?.data ?? []}
            rowKey="id"
            loading={authLoading || isLoading}
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
      </div>
    </PageLayout>
  );
}