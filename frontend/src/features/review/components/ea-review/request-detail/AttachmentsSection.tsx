'use client';

import { Button } from 'antd';
import { DataTable } from '@/shared/components/ui/DataTable';
import { RequestDetailSection } from '@/features/review/components/ea-review/request-detail/RequestDetailSection';

export function AttachmentsSection({
  attachments,
  attachmentColumns,
  canManageAttachments,
  onUpload,
}: {
  attachments: any[];
  attachmentColumns: any[];
  canManageAttachments: boolean;
  onUpload: () => void;
}) {
  return (
    <RequestDetailSection title="Attachments" defaultOpen={false} badge={attachments?.length}>
      {canManageAttachments && (
        <div className="mb-3">
          <Button type="primary" onClick={onUpload}>
            Upload Attachment
          </Button>
        </div>
      )}
      {attachments && attachments.length > 0 ? (
        <DataTable columns={attachmentColumns} data={attachments} rowKey="id" />
      ) : (
        <div className="text-center py-4 text-sm text-text-secondary">No attachments</div>
      )}
    </RequestDetailSection>
  );
}
