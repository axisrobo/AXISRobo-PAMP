'use client';

import { Card, Tooltip } from 'antd';
import { CloudUploadOutlined, QuestionCircleOutlined } from '@ant-design/icons';

import { type UploadedAttachment } from '@/features/review/components/ea-review/request-create/DiagramUploadCard';
import { TechnicalArchitectureUploadCard } from './TechnicalArchitectureUploadCard';

type TechnicalArchitectureDiagramSectionProps = {
  requestId: string | null;
  attachments: UploadedAttachment[];
  onChange: (attachments: UploadedAttachment[]) => void;
  readOnly?: boolean;
};

function UploadDisabledPlaceholder() {
  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center text-gray-400">
      <CloudUploadOutlined style={{ fontSize: 32, color: '#bbb' }} />
      <div className="mt-2">Please save Step 01 first to enable upload</div>
    </div>
  );
}

export function TechnicalArchitectureDiagramSection({
  requestId,
  attachments,
  onChange,
  readOnly = false,
}: TechnicalArchitectureDiagramSectionProps) {
  return (
    <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-red-500">*</span>
        <h3 className="font-semibold text-sm">Technical Architecture Diagram</h3>
        <Tooltip title="Upload your technical architecture diagram for EA review">
          <QuestionCircleOutlined className="text-gray-400" />
        </Tooltip>
      </div>

      {requestId ? (
        <TechnicalArchitectureUploadCard
          requestId={requestId}
          attachments={attachments}
          onChange={onChange}
          readOnly={readOnly}
        />
      ) : (
        <UploadDisabledPlaceholder />
      )}

      <div className="text-xs text-gray-400 space-y-0.5" style={{ marginTop: 31 }}>
        <p>This is a self-service agent for technical architecture review. Please upload your architecture diagram. The diagram should not contain sensitive information such as IP addresses.</p>
        <p>The score is for reference only. Some recognition may be inaccurate. If the score is below 7, please consider further optimization. If the score is 7 or above, you can move to the next step.</p>
        <p>You can try AI multiple times. Please keep only the final required files and delete any unnecessary ones before your submission.</p>
      </div>
    </Card>
  );
}