'use client';

import { DiagramUploadCard, type UploadedAttachment } from '@/features/review/components/ea-review/request-create/DiagramUploadCard';

type ApplicationArchitectureUploadCardProps = {
  requestId: string;
  attachments: UploadedAttachment[];
  onChange: (attachments: UploadedAttachment[]) => void;
  readOnly?: boolean;
};

export function ApplicationArchitectureUploadCard({
  requestId,
  attachments,
  onChange,
  readOnly = false,
}: ApplicationArchitectureUploadCardProps) {
  return (
    <DiagramUploadCard
      requestId={requestId}
      bizType="App_Arch"
      showArchTypeRadio
      attachments={attachments}
      onChange={onChange}
      readOnly={readOnly}
    />
  );
}