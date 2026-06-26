'use client';

import { useParams, useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/shared/lib/api';
import { useT } from '@/shared/lib/locale';
import { StatusBadge } from '@/shared/components/ui/StatusBadge';
import { DataTable } from '@/shared/components/ui/DataTable';
import { useAuth } from '@/shared/lib/auth-context';
import { AppArchReportDrawer } from '@/features/review/components/ea-review/request-detail/AppArchReportDrawer';
import { TechArchReportDrawer } from '@/features/review/components/ea-review/request-detail/TechArchReportDrawer';
import { RequestDetailSection } from '@/features/review/components/ea-review/request-detail/RequestDetailSection';
import { AttachmentsSection } from '@/features/review/components/ea-review/request-detail/AttachmentsSection';
import { GeneralDataSection } from '@/features/review/components/ea-review/request-detail/GeneralDataSection';
import { AVDMLifecycleStageSection } from '@/features/review/components/ea-review/request-detail/AVDMLifecycleStageSection';
import { AVDMConcernListSection, type AVDMEvaluation } from '@/features/review/components/ea-review/request-detail/AVDMConcernListSection';
import { AVDMConcernExpandSection } from '@/features/review/components/ea-review/request-detail/AVDMConcernExpandSection';
import { AVDMViewpointExpandSection } from '@/features/review/components/ea-review/request-detail/AVDMViewpointExpandSection';
import { AVDMArtifactExpandSection } from '@/features/review/components/ea-review/request-detail/AVDMArtifactExpandSection';
import { AddApplicationModal } from '@/features/review/components/ea-review/request-detail/modals/AddApplicationModal';
import { AddInterfaceModal } from '@/features/review/components/ea-review/request-detail/modals/AddInterfaceModal';
import { UploadAttachmentModal } from '@/features/review/components/ea-review/request-detail/modals/UploadAttachmentModal';
import { ImageViewerModal } from '@/features/review/components/ea-review/request-detail/modals/ImageViewerModal';
import { useArchCheckModals } from '@/features/review/components/ea-review/request-detail/hooks/useArchCheckModals';
import { useRequestAttachments } from '@/features/review/components/ea-review/request-detail/hooks/useRequestAttachments';
import { useRequestAiDetail } from '@/features/review/components/ea-review/request-detail/hooks/useRequestAiDetail';
import {
  createAttachmentColumns,
  createDiagramColumns,
} from '@/features/review/components/ea-review/request-detail/requestDetailColumns';
import { ArchitectureLifecycleStage, normalizeAVDMWorkflowStatus } from '@/shared/lib/avdmWorkflowStatus';
import { Button, Empty, Skeleton, Tabs, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

type AVDMWorkflowStatusResponse = {
  projectId: string;
  currentStatus: string;
  architectureLifecycleStage: ArchitectureLifecycleStage;
  architectureLifecycleStages: ArchitectureLifecycleStage[];
};

type ArtifactSelectionItem = {
  concernKey: string;
  artifactName: string;
  rationale?: string | null;
};

type AVDMAssessmentRecord = {
  concernRequirementConfirmedAt?: string | null;
  evaluation?: AVDMEvaluation | null;
  artifactSelection?: ArtifactSelectionItem[] | null;
};

export default function RequestDetailView() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? '';
  const router = useRouter();
  const t = useT();
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();

  const {
    addAppOpen,
    setAddAppOpen,
    editAppRecord,
    setEditAppRecord,
    addAppForm,
    setAddAppForm,
    addAppErrors,
    setAddAppErrors,
    appSearchKeyword,
    setAppSearchKeyword,
    openAddApp,
    openEditApp,
    closeAppModal,
    saveAppModal,
    addIntfOpen,
    setAddIntfOpen,
    editIntfRecord,
    setEditIntfRecord,
    addIntfForm,
    setAddIntfForm,
    addIntfErrors,
    setAddIntfErrors,
    intfSourceSearchKeyword,
    setIntfSourceSearchKeyword,
    intfTargetSearchKeyword,
    setIntfTargetSearchKeyword,
    openAddInterface,
    openEditInterface,
    closeInterfaceModal,
    saveInterfaceModal,
  } = useArchCheckModals();

  const attachmentsState = useRequestAttachments(id, messageApi);
  const aiDetailState = useRequestAiDetail(messageApi, {
    addAppOpen,
    setAddAppOpen,
    setEditAppRecord,
    appSearchKeyword,
    addIntfOpen,
    setAddIntfOpen,
    setEditIntfRecord,
    setAddIntfForm,
    setAddIntfErrors,
    intfSourceSearchKeyword,
    intfTargetSearchKeyword,
    setIntfSourceSearchKeyword,
    setIntfTargetSearchKeyword,
  });

  const { user, hasRole } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ['eaRequest', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}`),
    enabled: !!id,
  });

  const projectId = data?.projectId;
  const { data: workflowStatus, isLoading: workflowStatusLoading } = useQuery({
    queryKey: ['avdmWorkflowStatus', projectId],
    queryFn: () => api.get<AVDMWorkflowStatusResponse>(`/avdm/projects/${encodeURIComponent(projectId)}/workflow-status`),
    enabled: !!projectId,
  });
  const { data: avdmAssessment, isLoading: avdmAssessmentLoading } = useQuery({
    queryKey: ['avdmAssessment', projectId],
    queryFn: () => api.get<AVDMAssessmentRecord>(`/avdm/projects/${encodeURIComponent(projectId)}`),
    enabled: !!projectId,
  });

  const { data: concernsData, isLoading: concernsLoading } = useQuery({
    queryKey: ['eaRequestConcerns', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}/concerns`),
    enabled: !!id,
  });

  const { data: artifactsData, isLoading: artifactsLoading } = useQuery({
    queryKey: ['eaRequestArtifacts', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}/artifacts`),
    enabled: !!id,
  });

  const { data: viewpointsData, isLoading: viewpointsLoading } = useQuery({
    queryKey: ['eaRequestViewpoints', id],
    queryFn: () => api.get<any>(`/ea-requests/${id}/viewpoints`),
    enabled: !!id,
  });

  const confirmConcernsMutation = useMutation({
    mutationFn: () => api.post<AVDMWorkflowStatusResponse>(`/avdm/projects/${encodeURIComponent(projectId)}/concerns/confirm`, {
      operator: user?.id || 'system',
    }),
    onSuccess: () => {
      messageApi.success('Concern requirements confirmed');
      queryClient.invalidateQueries({ queryKey: ['avdmWorkflowStatus', projectId] });
      queryClient.invalidateQueries({ queryKey: ['avdmAssessment', projectId] });
      queryClient.invalidateQueries({ queryKey: ['eaRequest', id] });
    },
    onError: (error: Error) => {
      messageApi.error(error?.message || 'Failed to confirm concerns');
    },
  });

  const confirmArtifactRequirementsMutation = useMutation({
    mutationFn: () => api.post(`/avdm/projects/${encodeURIComponent(projectId)}/artifacts/requirements/confirm`, {
      operator: user?.id || 'system',
    }),
    onSuccess: () => {
      messageApi.success('Artifact requirements confirmed');
      queryClient.invalidateQueries({ queryKey: ['avdmWorkflowStatus', projectId] });
      queryClient.invalidateQueries({ queryKey: ['avdmAssessment', projectId] });
    },
    onError: (error: Error) => {
      messageApi.error(error?.message || 'Failed to confirm artifact requirements');
    },
  });

  const submitArtifactsMutation = useMutation({
    mutationFn: () => api.put(`/avdm/projects/${encodeURIComponent(projectId)}/artifacts`, {
      operator: user?.id || 'system',
      selections: avdmAssessment?.artifactSelection ?? [],
    }),
    onSuccess: () => {
      messageApi.success('Artifacts submitted');
      queryClient.invalidateQueries({ queryKey: ['avdmWorkflowStatus', projectId] });
      queryClient.invalidateQueries({ queryKey: ['avdmAssessment', projectId] });
    },
    onError: (error: Error) => {
      messageApi.error(error?.message || 'Failed to submit artifacts');
    },
  });

  const confirmQuestionnaireMutation = useMutation({
    mutationFn: () => api.post(`/avdm/projects/${encodeURIComponent(projectId)}/questionnaire/confirm`, {
      operator: user?.id || 'system',
    }),
    onSuccess: () => {
      messageApi.success('Questionnaire confirmed');
      queryClient.invalidateQueries({ queryKey: ['avdmWorkflowStatus', projectId] });
      queryClient.invalidateQueries({ queryKey: ['avdmAssessment', projectId] });
    },
    onError: (error: Error) => {
      messageApi.error(error?.message || 'Failed to confirm questionnaire');
    },
  });

  const {
    aiDetail,
    aiDrawerTab,
    setAiDrawerTab,
    aiIssueFilter,
    setAiIssueFilter,
    viewerOpen,
    setViewerOpen,
    viewerSrc,
    setViewerSrc,
    appPage,
    setAppPage,
    appPageSize,
    setAppPageSize,
    appSelectedKeys,
    setAppSelectedKeys,
    intfPage,
    setIntfPage,
    intfPageSize,
    setIntfPageSize,
    intfSelectedKeys,
    setIntfSelectedKeys,
    cmdbApps,
    cmdbFetching,
    intfSourceApps,
    intfSourceFetching,
    intfTargetApps,
    intfTargetFetching,
    archCheckApps,
    archCheckAppsFetching,
    archCheckInteractions,
    archCheckInteractionsFetching,
    updateArchCheckApp,
    deleteArchCheckApp,
    addArchCheckApp,
    addArchCheckInteraction,
    updateArchCheckInteraction,
    deleteArchCheckInteraction,
    confirmArchCheckApps,
    confirmArchCheckInteractions,
    handleOpenAiDetail,
    handleCloseAiDrawer,
  } = aiDetailState;

  if (isLoading) {
    return <div className="p-6"><Skeleton active paragraph={{ rows: 8 }} /></div>;
  }

  if (!data) {
    return (
      <div className="p-6 text-center py-12">
        <Empty description="Request not found." />
        <Button type="link" onClick={() => router.back()} style={{ marginTop: 16 }}>Go Back</Button>
      </div>
    );
  }

  const isAdmin = hasRole('ea_admin');
  const isReviewer = hasRole('ea_reviewer');
  const completedStatuses = ['Completed', 'Approved', 'Approved with Actions', 'Rejected'];
  const isRequestOwner = !!user?.id && data.requestorName === user.id;
  const normalizedWorkflowStatus = workflowStatus
    ? normalizeAVDMWorkflowStatus(workflowStatus.currentStatus)
    : null;
  const canManageAttachments = isAdmin || isReviewer || (isRequestOwner && !completedStatuses.includes(data.status));
  const canConfirmConcerns = (isAdmin || isReviewer)
    && !!projectId
    && !!workflowStatus
    && ['questionnaire_submitted', 'questionnaire_confirmed'].includes(workflowStatus.currentStatus);

  const canConfirmArtifactRequirements = (isAdmin || isReviewer)
    && !!projectId
    && !!workflowStatus
    && workflowStatus.currentStatus === 'concern_requirement_confirmed';

  const canSubmitArtifacts = (isAdmin || isReviewer)
    && !!projectId
    && !!workflowStatus
    && workflowStatus.currentStatus === 'artifact_requirement_confirmed';

  const canConfirmQuestionnaire = (isAdmin || isReviewer)
    && !!projectId
    && !!workflowStatus
    && workflowStatus.currentStatus === 'questionnaire_submitted';
  const canGoToQuestionnaireSubmit = !!id
    && (isAdmin || isRequestOwner)
    && normalizedWorkflowStatus === 'request_created';

  const attachmentColumns = createAttachmentColumns({
    canManageAttachments,
    onDownloadAttachment: attachmentsState.handleDownloadAttachment,
    onDeleteAttachment: attachmentsState.handleDeleteAttachment,
  });
  const diagramColumns = createDiagramColumns({
    bizType: 'App_Arch',
    onOpenAiDetail: handleOpenAiDetail,
    onDownloadAttachment: attachmentsState.handleDownloadAttachment,
  });
  const techDiagramColumns = createDiagramColumns({
    bizType: 'Tech_Arch',
    onOpenAiDetail: handleOpenAiDetail,
    onDownloadAttachment: attachmentsState.handleDownloadAttachment,
  });

  const getDiagramSequence = (diagram: any) => {
    const fileName = String(diagram?.fileName || diagram?.attachmentName || '');
    const match = fileName.match(/^(\d+)-/);
    return match ? Number(match[1]) : null;
  };

  const sortedTechDiagrams = [...(data.techDiagrams ?? [])].sort((a, b) => {
    const sequenceA = getDiagramSequence(a);
    const sequenceB = getDiagramSequence(b);
    if (sequenceA != null || sequenceB != null) {
      return (sequenceB ?? -1) - (sequenceA ?? -1);
    }

    return new Date(b.evaluatedAt ?? b.createdAt ?? 0).getTime() - new Date(a.evaluatedAt ?? a.createdAt ?? 0).getTime();
  });

  const sortedTechDiagramColumns = techDiagramColumns.map((column) =>
    column.key === 'no'
      ? {
          ...column,
          render: (_value: any, row: any, index: number) => getDiagramSequence(row) ?? (sortedTechDiagrams.length - (index ?? 0)),
        }
      : column
  );

  return (
    <div className="p-6">
      {contextHolder}

      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => router.back()} />
          <h1 className="text-lg font-semibold text-text-primary">Request Details</h1>
          <StatusBadge status={data.status} />
        </div>
      </div>

      <GeneralDataSection data={data} />

      <AVDMLifecycleStageSection
        workflowStatus={workflowStatus ? {
          ...workflowStatus,
          concernRequirementConfirmedAt: avdmAssessment?.concernRequirementConfirmedAt ?? null,
        } : undefined}
        loading={workflowStatusLoading}
        canConfirmConcerns={canConfirmConcerns}
        confirmingConcerns={confirmConcernsMutation.isPending}
        onConfirmConcerns={() => confirmConcernsMutation.mutate()}
        canConfirmArtifactRequirements={canConfirmArtifactRequirements}
        confirmingArtifactRequirements={confirmArtifactRequirementsMutation.isPending}
        onConfirmArtifactRequirements={() => confirmArtifactRequirementsMutation.mutate()}
        canSubmitArtifacts={canSubmitArtifacts}
        submittingArtifacts={submitArtifactsMutation.isPending}
        onSubmitArtifacts={() => submitArtifactsMutation.mutate()}
        canConfirmQuestionnaire={canConfirmQuestionnaire}
        confirmingQuestionnaire={confirmQuestionnaireMutation.isPending}
        onConfirmQuestionnaire={() => confirmQuestionnaireMutation.mutate()}
      />

      {canGoToQuestionnaireSubmit && (
        <div className="mt-3 mb-4 flex items-center justify-between rounded-md border border-blue-200 bg-blue-50 px-3 py-2">
          <div className="text-xs text-text-secondary">
            Questionnaire is not submitted yet. Project team should complete Step 2 before review team confirmation.
          </div>
          <Button type="primary" size="small" onClick={() => router.push(`/ea-review/request/create?id=${id}`)}>
            Go to Questionnaire Submit
          </Button>
        </div>
      )}

      <Tabs defaultActiveKey="concerns" items={[
        {
          key: 'concerns',
          label: `Architecture Concerns (${concernsData?.concerns?.length ?? 0})`,
          children: (
            <AVDMConcernExpandSection
              concerns={concernsData?.concerns ?? []}
              loading={concernsLoading}
            />
          ),
        },
        {
          key: 'viewpoints',
          label: `Architecture Viewpoints (${viewpointsData?.viewpoints?.length ?? 0})`,
          children: (
            <AVDMViewpointExpandSection
              viewpoints={viewpointsData?.viewpoints ?? []}
              loading={viewpointsLoading}
            />
          ),
        },
        {
          key: 'artifacts',
          label: `Architecture Artifacts (${artifactsData?.artifacts?.length ?? 0})`,
          children: (
            <AVDMArtifactExpandSection
              artifacts={artifactsData?.artifacts ?? []}
              loading={artifactsLoading}
            />
          ),
        },
      ]} />

      <AttachmentsSection
        attachments={[...(data.attachments ?? [])].sort((a, b) => new Date(b.createdAt ?? 0).getTime() - new Date(a.createdAt ?? 0).getTime())}
        attachmentColumns={attachmentColumns}
        canManageAttachments={canManageAttachments}
        onUpload={attachmentsState.handleOpenUploadAttachmentModal}
      />

      <RequestDetailSection title="Application Architecture Diagram">
        {data.appDiagrams && data.appDiagrams.length > 0 ? (
          <DataTable
            columns={diagramColumns}
            data={[...data.appDiagrams].sort((a, b) => new Date(b.evaluatedAt ?? 0).getTime() - new Date(a.evaluatedAt ?? 0).getTime())}
            rowKey="id"
          />
        ) : (
          <div className="py-4 text-center text-sm text-text-secondary">No diagrams uploaded</div>
        )}
      </RequestDetailSection>

      <RequestDetailSection title="Technical Architecture Diagram">
        {data.techDiagrams && data.techDiagrams.length > 0 ? (
          <DataTable columns={sortedTechDiagramColumns} data={sortedTechDiagrams} rowKey="id" />
        ) : (
          <div className="py-4 text-center text-sm text-text-secondary">No diagrams uploaded</div>
        )}
      </RequestDetailSection>

      <TechArchReportDrawer
        open={!!aiDetail && aiDetail?._bizType === 'Tech_Arch'}
        aiDetail={aiDetail?._bizType === 'Tech_Arch' ? aiDetail : null}
        t={t}
        aiIssueFilter={aiIssueFilter}
        setAiIssueFilter={setAiIssueFilter}
        onClose={handleCloseAiDrawer}
      />
      <AppArchReportDrawer
        open={!!aiDetail && aiDetail?._bizType !== 'Tech_Arch'}
        aiDetail={aiDetail?._bizType !== 'Tech_Arch' ? aiDetail : null}
        t={t}
        aiDrawerTab={aiDrawerTab}
        setAiDrawerTab={setAiDrawerTab}
        aiIssueFilter={aiIssueFilter}
        setAiIssueFilter={setAiIssueFilter}
        setViewerSrc={setViewerSrc}
        setViewerOpen={setViewerOpen}
        onClose={handleCloseAiDrawer}
        archCheckApps={archCheckApps}
        archCheckAppsFetching={archCheckAppsFetching}
        archCheckInteractions={archCheckInteractions}
        archCheckInteractionsFetching={archCheckInteractionsFetching}
        appPage={appPage}
        appPageSize={appPageSize}
        setAppPage={setAppPage}
        setAppPageSize={setAppPageSize}
        appSelectedKeys={appSelectedKeys}
        setAppSelectedKeys={setAppSelectedKeys}
        confirmArchCheckApps={confirmArchCheckApps}
        deleteArchCheckApp={deleteArchCheckApp}
        onOpenAddApp={openAddApp}
        onOpenEditApp={openEditApp}
        intfPage={intfPage}
        intfPageSize={intfPageSize}
        setIntfPage={setIntfPage}
        setIntfPageSize={setIntfPageSize}
        intfSelectedKeys={intfSelectedKeys}
        setIntfSelectedKeys={setIntfSelectedKeys}
        confirmArchCheckInteractions={confirmArchCheckInteractions}
        deleteArchCheckInteraction={deleteArchCheckInteraction}
        onOpenAddInterface={openAddInterface}
        onOpenEditInterface={openEditInterface}
      />

      <UploadAttachmentModal
        open={attachmentsState.uploadAttachmentOpen}
        uploadAttachmentFile={attachmentsState.uploadAttachmentFile}
        setUploadAttachmentFile={attachmentsState.setUploadAttachmentFile}
        isPending={attachmentsState.uploadAttachmentMutation.isPending}
        onCancel={attachmentsState.handleCloseUploadAttachmentModal}
        onSave={attachmentsState.handleSaveUploadAttachment}
      />

      <AddApplicationModal
        open={addAppOpen}
        editAppRecord={editAppRecord}
        t={t}
        addAppForm={addAppForm}
        setAddAppForm={setAddAppForm}
        addAppErrors={addAppErrors}
        setAddAppErrors={setAddAppErrors}
        cmdbFetching={cmdbFetching}
        cmdbApps={cmdbApps}
        setAppSearchKeyword={setAppSearchKeyword}
        saveLoading={editAppRecord ? updateArchCheckApp.isPending : addArchCheckApp.isPending}
        onCancel={closeAppModal}
        onSave={() => saveAppModal(aiDetail?._aiCheckId, updateArchCheckApp, addArchCheckApp)}
      />

      <AddInterfaceModal
        open={addIntfOpen}
        editIntfRecord={editIntfRecord}
        t={t}
        addIntfForm={addIntfForm}
        setAddIntfForm={setAddIntfForm}
        addIntfErrors={addIntfErrors}
        setAddIntfErrors={setAddIntfErrors}
        intfSourceFetching={intfSourceFetching}
        intfTargetFetching={intfTargetFetching}
        intfSourceApps={intfSourceApps}
        intfTargetApps={intfTargetApps}
        setIntfSourceSearchKeyword={setIntfSourceSearchKeyword}
        setIntfTargetSearchKeyword={setIntfTargetSearchKeyword}
        saveLoading={editIntfRecord ? updateArchCheckInteraction.isPending : addArchCheckInteraction.isPending}
        onCancel={closeInterfaceModal}
        onSave={() => saveInterfaceModal(aiDetail?._aiCheckId, updateArchCheckInteraction, addArchCheckInteraction)}
      />

      <ImageViewerModal open={viewerOpen} viewerSrc={viewerSrc} onClose={() => setViewerOpen(false)} />
    </div>
  );
}
