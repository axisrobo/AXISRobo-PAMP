export type AVDMWorkflowStatus =
  | 'request_created'
  | 'questionnaire_submitted'
  | 'questionnaire_confirmed'
  | 'concern_requirement_confirmed'
  | 'artifact_requirement_confirmed'
  | 'artifact_submitted';

export type ArchitectureLifecycleStage = 'Preparation' | 'Design' | 'Review' | 'Execution & Operations';

export const architectureLifecycleStages: ArchitectureLifecycleStage[] = [
  'Preparation',
  'Design',
  'Review',
  'Execution & Operations',
];

export type AVDMWorkflowPhase = 'Preparation';

export const avdmWorkflowStatuses: AVDMWorkflowStatus[] = [
  'request_created',
  'questionnaire_submitted',
  'questionnaire_confirmed',
  'concern_requirement_confirmed',
  'artifact_requirement_confirmed',
  'artifact_submitted',
];

export const avdmWorkflowPhaseMap: Record<AVDMWorkflowStatus, AVDMWorkflowPhase> = {
  request_created: 'Preparation',
  questionnaire_submitted: 'Preparation',
  questionnaire_confirmed: 'Preparation',
  concern_requirement_confirmed: 'Preparation',
  artifact_requirement_confirmed: 'Preparation',
  artifact_submitted: 'Preparation',
};

export const avdmWorkflowLabelMap: Record<AVDMWorkflowStatus, string> = {
  request_created: 'Preparation - Request Created',
  questionnaire_submitted: 'Preparation - Questionnaire Submitted',
  questionnaire_confirmed: 'Preparation - Questionnaire Confirmed',
  concern_requirement_confirmed: 'Preparation - Concern Requirement Confirmed',
  artifact_requirement_confirmed: 'Preparation - Artifact Requirement Confirmed',
  artifact_submitted: 'Preparation - Artifact Submitted',
};

const workflowStatusAlias: Record<string, AVDMWorkflowStatus> = {
  requestcreated: 'request_created',
  request_created: 'request_created',
  questionnairesubmitted: 'questionnaire_submitted',
  questionnaire_submitted: 'questionnaire_submitted',
  questionnaresubmited: 'questionnaire_submitted',
  questionnairesubmited: 'questionnaire_submitted',
  questionnare_submited: 'questionnaire_submitted',
  questionnaireconfirmed: 'questionnaire_confirmed',
  questionnaire_confirmed: 'questionnaire_confirmed',
  questionnareconfirmed: 'questionnaire_confirmed',
  concernrequirementconfirmed: 'concern_requirement_confirmed',
  concern_requirement_confirmed: 'concern_requirement_confirmed',
  concernrequiremendconfirmed: 'concern_requirement_confirmed',
  artifactrequirementconfirmed: 'artifact_requirement_confirmed',
  artifact_requirement_confirmed: 'artifact_requirement_confirmed',
  artifactrequiremendconfirmed: 'artifact_requirement_confirmed',
  artifactsubmitted: 'artifact_submitted',
  artifact_submitted: 'artifact_submitted',
};

export function normalizeAVDMWorkflowStatus(status: string): AVDMWorkflowStatus | null {
  if (!status) return null;
  const compact = status.trim().toLowerCase().replace(/[\s-]+/g, '_');
  const canonical = compact.replace(/[^a-z0-9_]/g, '');
  return workflowStatusAlias[canonical] ?? null;
}

export function getAVDMWorkflowPresentation(status: string): {
  normalized: AVDMWorkflowStatus;
  phase: AVDMWorkflowPhase;
  label: string;
} | null {
  const normalized = normalizeAVDMWorkflowStatus(status);
  if (!normalized) return null;
  return {
    normalized,
    phase: avdmWorkflowPhaseMap[normalized],
    label: avdmWorkflowLabelMap[normalized],
  };
}
