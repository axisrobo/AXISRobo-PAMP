'use client';

import { DiagramUploadCard, type UploadedAttachment } from '@/features/review/components/ea-review/request-create/DiagramUploadCard';

type TechnicalArchitectureUploadCardProps = {
  requestId: string;
  attachments: UploadedAttachment[];
  onChange: (attachments: UploadedAttachment[]) => void;
  readOnly?: boolean;
};

export function TechnicalArchitectureUploadCard({
  requestId,
  attachments,
  onChange,
  readOnly = false,
}: TechnicalArchitectureUploadCardProps) {
  return (
    <DiagramUploadCard
      requestId={requestId}
      bizType="Tech_Arch"
      attachments={attachments}
      onChange={onChange}
      readOnly={readOnly}
    />
  );
}