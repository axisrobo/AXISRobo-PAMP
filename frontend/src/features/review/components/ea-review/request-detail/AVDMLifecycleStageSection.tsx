'use client';

import { Skeleton } from 'antd';
import { Button } from 'antd';

import {
  ArchitectureLifecycleStage,
  architectureLifecycleStages,
  getAVDMWorkflowPresentation,
} from '@/shared/lib/avdmWorkflowStatus';
import { RequestDetailSection } from '@/features/review/components/ea-review/request-detail/RequestDetailSection';

type AVDMWorkflowStatusResponse = {
  projectId: string;
  currentStatus: string;
  architectureLifecycleStage: ArchitectureLifecycleStage;
  architectureLifecycleStages: ArchitectureLifecycleStage[];
  concernRequirementConfirmedAt?: string | null;
};

function getStageCardClass(isCurrent: boolean, isCompleted: boolean) {
  if (isCurrent) {
    return 'border-primary-blue bg-blue-50 text-primary-blue';
  }
  if (isCompleted) {
    return 'border-green-500 bg-green-50 text-green-700';
  }
  return 'border-border-default bg-white text-text-secondary';
}

export function AVDMLifecycleStageSection({
  workflowStatus,
  loading,
  canConfirmConcerns = false,
  confirmingConcerns = false,
  onConfirmConcerns,
  canConfirmArtifactRequirements = false,
  confirmingArtifactRequirements = false,
  onConfirmArtifactRequirements,
  canSubmitArtifacts = false,
  submittingArtifacts = false,
  onSubmitArtifacts,
  canConfirmQuestionnaire = false,
  confirmingQuestionnaire = false,
  onConfirmQuestionnaire,
}: {
  workflowStatus?: AVDMWorkflowStatusResponse;
  loading: boolean;
  canConfirmConcerns?: boolean;
  confirmingConcerns?: boolean;
  onConfirmConcerns?: () => void;
  canConfirmArtifactRequirements?: boolean;
  confirmingArtifactRequirements?: boolean;
  onConfirmArtifactRequirements?: () => void;
  canSubmitArtifacts?: boolean;
  submittingArtifacts?: boolean;
  onSubmitArtifacts?: () => void;
  canConfirmQuestionnaire?: boolean;
  confirmingQuestionnaire?: boolean;
  onConfirmQuestionnaire?: () => void;
}) {
  const stages = workflowStatus?.architectureLifecycleStages?.length
    ? workflowStatus.architectureLifecycleStages
    : architectureLifecycleStages;
  const currentStage = workflowStatus?.architectureLifecycleStage ?? 'Preparation';
  const currentStageIndex = stages.indexOf(currentStage);
  const workflowPresentation = workflowStatus
    ? getAVDMWorkflowPresentation(workflowStatus.currentStatus)
    : null;
  const concernConfirmedAt = workflowStatus?.concernRequirementConfirmedAt
    ? new Date(workflowStatus.concernRequirementConfirmedAt).toLocaleString()
    : null;

  return (
    <RequestDetailSection title="Architecture Lifecycle" defaultOpen>
      {loading ? (
        <Skeleton active paragraph={{ rows: 2 }} />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {stages.map((stage, index) => {
              const isCurrent = index === currentStageIndex;
              const isCompleted = currentStageIndex > -1 && index < currentStageIndex;
              return (
                <div
                  key={stage}
                  className={`rounded-md border px-3 py-2 transition-colors ${getStageCardClass(isCurrent, isCompleted)}`}
                >
                  <div className="text-xs uppercase tracking-wide opacity-80">Stage {index + 1}</div>
                  <div className="text-sm font-semibold mt-1">{stage}</div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 text-xs text-text-secondary">
            Current AVDM step:{' '}
            <span className="font-semibold text-text-primary">
              {workflowPresentation?.label ?? 'Preparation - Request Created'}
            </span>
          </div>

          <div className="mt-1 text-xs text-text-secondary">
            Concern confirmation:{' '}
            <span className="font-semibold text-text-primary">
              {concernConfirmedAt ?? 'Pending review team confirmation'}
            </span>
          </div>

          {canConfirmConcerns && onConfirmConcerns && (
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="text-xs text-text-secondary">
                Review team action: confirm concern requirements after questionnaire submission.
              </div>
              <Button
                type="primary"
                size="small"
                loading={confirmingConcerns}
                onClick={onConfirmConcerns}
              >
                Confirm Concerns
              </Button>
            </div>
          )}

          {canConfirmArtifactRequirements && onConfirmArtifactRequirements && (
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="text-xs text-text-secondary">
                Review team action: confirm artifact requirements after concerns confirmed.
              </div>
              <Button
                type="primary"
                size="small"
                loading={confirmingArtifactRequirements}
                onClick={onConfirmArtifactRequirements}
              >
                Confirm Artifact Requirements
              </Button>
            </div>
          )}

          {canSubmitArtifacts && onSubmitArtifacts && (
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="text-xs text-text-secondary">
                Review team action: submit artifact selection.
              </div>
              <Button
                type="primary"
                size="small"
                loading={submittingArtifacts}
                onClick={onSubmitArtifacts}
              >
                Submit Artifacts
              </Button>
            </div>
          )}

          {canConfirmQuestionnaire && onConfirmQuestionnaire && (
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="text-xs text-text-secondary">
                Review team action: confirm questionnaire.
              </div>
              <Button
                type="primary"
                size="small"
                loading={confirmingQuestionnaire}
                onClick={onConfirmQuestionnaire}
              >
                Confirm Questionnaire
              </Button>
            </div>
          )}
        </>
      )}
    </RequestDetailSection>
  );
}
