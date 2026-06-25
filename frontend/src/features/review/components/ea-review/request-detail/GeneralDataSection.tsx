'use client';

import { RequestDetailSection } from '@/features/review/components/ea-review/request-detail/RequestDetailSection';

const ORGANIZATION_LABELS: Record<string, string> = {
  DTIT: 'I am from DT/IT',
  other: 'I am from other internal organization',
};

function formatOrganizationLabel(value?: string | null) {
  if (!value) return value;
  return ORGANIZATION_LABELS[value] || value;
}

function GeneralDataRow({
  label,
  value,
  bold,
  link,
}: {
  label: string;
  value?: string | null;
  bold?: boolean;
  link?: boolean;
}) {
  return (
    <div className="flex py-2 border-b border-gray-50 last:border-0">
      <span className="text-xs text-text-secondary w-44 shrink-0 text-right pr-3">{label}:</span>
      {link && value ? (
        <a href={value} target="_blank" rel="noreferrer" className="text-sm text-primary-blue hover:underline break-all">{value}</a>
      ) : (
        <span className={`text-sm text-text-primary ${bold ? 'font-semibold' : ''}`}>{value || '-'}</span>
      )}
    </div>
  );
}

export function GeneralDataSection({ data }: { data: any }) {
  return (
    <RequestDetailSection title="General Data">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12">
        <div>
          <GeneralDataRow label="Request ID" value={data.requestId} bold />
          <GeneralDataRow label="Project ID" value={data.projectId} />
          <GeneralDataRow label="Project Name" value={data.projectName} />
          <GeneralDataRow label="Review Scope" value={data.scope} />
          <GeneralDataRow label="WS Name / Phase Name" value={data.wsPhase} />
          <GeneralDataRow label="Request Status" value={data.status} bold />
          <GeneralDataRow label="Confluence Page (Link)" value={data.link} link />
        </div>
        <div>
          <GeneralDataRow label="EA Review Result" value={data.reviewResult} bold />
          <GeneralDataRow label="PM" value={data.pmName} />
          <GeneralDataRow label="Biz Analyst" value={data.dtLeadName} />
          <GeneralDataRow label="IT Lead" value={data.itLeadName} />
          <GeneralDataRow label="Requestor" value={data.requestorName} />
          <GeneralDataRow label="Organization" value={formatOrganizationLabel(data.organization)} />
          <GeneralDataRow label="Assigned Reviewer" value={data.reviewerName} />
          <GeneralDataRow label="Description" value={data.requestDesc} />
        </div>
      </div>
    </RequestDetailSection>
  );
}
