import { Tag } from 'antd';
import { getAVDMWorkflowPresentation } from '@/shared/lib/avdmWorkflowStatus';

interface StatusBadgeProps {
  status: string;
  variant?: 'badge' | 'text';
}

/**
 * Map project status strings to antd Tag preset colors.
 * Preset colors: success, processing, warning, error, default, plus named colors
 * like green, blue, orange, purple, red, etc.
 */
const statusTagColor: Record<string, string> = {
  Completed: 'green',
  Approved: 'green',
  Closed: 'green',
  Available: 'green',
  'In Progress': 'orange',
  Open: 'orange',
  'In Validation': 'orange',
  Submitted: 'blue',
  Draft: 'default',
  'Accepted by EA': 'purple',
  'Approved with Actions': 'cyan',
  Rejected: 'red',
  Booked: 'geekblue',
  Expired: 'volcano',
  request_created: 'default',
  questionnaire_submitted: 'blue',
  questionnaire_confirmed: 'cyan',
  concern_requirement_confirmed: 'purple',
  artifact_requirement_confirmed: 'geekblue',
  artifact_submitted: 'green',
};

const statusDisplayText: Record<string, string> = {
  request_created: 'Preparation - Request Created',
  questionnaire_submitted: 'Preparation - Questionnaire Submitted',
  questionnaire_confirmed: 'Preparation - Questionnaire Confirmed',
  concern_requirement_confirmed: 'Preparation - Concern Requirement Confirmed',
  artifact_requirement_confirmed: 'Preparation - Artifact Requirement Confirmed',
  artifact_submitted: 'Preparation - Artifact Submitted',
};

export function StatusBadge({ status, variant = 'badge' }: StatusBadgeProps) {
  const workflowPresentation = getAVDMWorkflowPresentation(status);
  const normalizedStatus = workflowPresentation?.normalized ?? status;
  const color = statusTagColor[normalizedStatus] || 'default';
  const displayText = workflowPresentation?.label || statusDisplayText[normalizedStatus] || status;

  if (variant === 'text') {
    return (
      <Tag color={color} variant="filled" style={{ background: 'transparent', paddingLeft: 0, paddingRight: 0 }}>
        {displayText}
      </Tag>
    );
  }

  return (
    <Tag color={color}>
      {displayText}
    </Tag>
  );
}
