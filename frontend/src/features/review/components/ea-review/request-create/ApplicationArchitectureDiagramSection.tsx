'use client';

import { Card, Tooltip } from 'antd';
import { CloudUploadOutlined, QuestionCircleOutlined } from '@ant-design/icons';

import { type UploadedAttachment } from '@/features/review/components/ea-review/request-create/DiagramUploadCard';
import { ApplicationArchitectureUploadCard } from './ApplicationArchitectureUploadCard';

type ApplicationArchitectureDiagramSectionProps = {
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

export function ApplicationArchitectureDiagramSection({
  requestId,
  attachments,
  onChange,
  readOnly = false,
}: ApplicationArchitectureDiagramSectionProps) {
  return (
    <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-red-500">*</span>
        <h3 className="font-semibold text-sm">Application Architecture Diagram</h3>
        <Tooltip title="Upload your application architecture diagram for EA review">
          <QuestionCircleOutlined className="text-gray-400" />
        </Tooltip>
      </div>

      {requestId ? (
        <ApplicationArchitectureUploadCard
          requestId={requestId}
          attachments={attachments}
          onChange={onChange}
          readOnly={readOnly}
        />
      ) : (
        <UploadDisabledPlaceholder />
      )}

      <div className="text-xs text-gray-400 space-y-0.5" style={{ marginTop: 31 }}>
        <p>This is a self-service agent for application architecture diagram inspection. Please select whether it is a New App Architecture or an E2E Solution Architecture, and upload the corresponding application architecture diagram image.</p>
        <p>The score and inspection are for reference only. There may be some inaccuracies in the recognition of the architecture diagram. If the score is below 7, please consider further optimization. If it is equal to or above 7, you can move to the next step.</p>
        <p>You can try AI multiple times. Please keep only the final required files and delete any unnecessary ones before your submission.</p>
      </div>
    </Card>
  );
}