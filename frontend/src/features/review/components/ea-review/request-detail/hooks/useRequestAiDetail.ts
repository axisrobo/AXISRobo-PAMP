'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';

export function useRequestAiDetail(messageApi: any, modals: any) {
  const queryClient = useQueryClient();
  const [aiDetail, setAiDetail] = useState<any>(null);
  const [aiDrawerTab, setAiDrawerTab] = useState<string>('score');
  const [aiIssueFilter, setAiIssueFilter] = useState<string[]>([]);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerSrc, setViewerSrc] = useState<string | null>(null);
  const [appPage, setAppPage] = useState(1);
  const [appPageSize, setAppPageSize] = useState(10);
  const [appSelectedKeys, setAppSelectedKeys] = useState<React.Key[]>([]);
  const [intfPage, setIntfPage] = useState(1);
  const [intfPageSize, setIntfPageSize] = useState(10);
  const [intfSelectedKeys, setIntfSelectedKeys] = useState<React.Key[]>([]);

  const { data: cmdbApps, isFetching: cmdbFetching } = useQuery({
    queryKey: ['cmdbAppSearch', modals.appSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: modals.appSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: modals.addAppOpen,
  });

  const { data: intfSourceApps, isFetching: intfSourceFetching } = useQuery({
    queryKey: ['cmdbAppSearch', 'intfSource', modals.intfSourceSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: modals.intfSourceSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: modals.addIntfOpen,
  });

  const { data: intfTargetApps, isFetching: intfTargetFetching } = useQuery({
    queryKey: ['cmdbAppSearch', 'intfTarget', modals.intfTargetSearchKeyword],
    queryFn: () => api.get<any>('/cmdb', { q: modals.intfTargetSearchKeyword || undefined, pageSize: 100, page: 1 }),
    enabled: modals.addIntfOpen,
  });

  const { data: archCheckApps, isFetching: archCheckAppsFetching } = useQuery({
    queryKey: ['archCheckApps', aiDetail?._aiCheckId],
    queryFn: () => api.get<any[]>('/arch-check-apps', { aiCheckId: aiDetail!._aiCheckId }),
    enabled: !!aiDetail?._aiCheckId && aiDrawerTab === 'applications',
  });

  const { data: archCheckInteractions, isFetching: archCheckInteractionsFetching } = useQuery({
    queryKey: ['archCheckInteractions', aiDetail?._aiCheckId],
    queryFn: () => api.get<any[]>('/arch-check-interactions', { aiCheckId: aiDetail!._aiCheckId }),
    enabled: !!aiDetail?._aiCheckId && aiDrawerTab === 'interfaces',
  });

  const updateArchCheckApp = useMutation({
    mutationFn: (payload: {
      checkAppUuid: string;
      appId: string;
      appName: string;
      idIsStandard: boolean;
      standardId?: string;
      functions?: string[];
      checkAppStatus: string;
      remark?: string;
    }) => api.put<any>(`/arch-check-apps/${payload.checkAppUuid}`, payload),
    onSuccess: () => {
      modals.setAddAppOpen(false);
      modals.setEditAppRecord(null);
      messageApi.success('Application updated successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to update application');
    },
  });

  const deleteArchCheckApp = useMutation({
    mutationFn: (checkAppUuid: string) => api.delete<any>(`/arch-check-apps/${checkAppUuid}`),
    onSuccess: () => {
      messageApi.success('Application deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to delete application');
    },
  });

  const addArchCheckApp = useMutation({
    mutationFn: (payload: {
      aiCheckId: string;
      appId: string;
      appName: string;
      idIsStandard: boolean;
      standardId?: string;
      functions?: string[];
      checkAppStatus: string;
      remark?: string;
    }) => api.post<any>('/arch-check-apps', payload),
    onSuccess: () => {
      modals.setAddAppOpen(false);
      messageApi.success('Application added successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to add application');
    },
  });

  const addArchCheckInteraction = useMutation({
    mutationFn: (payload: {
      aiCheckId: string;
      sourceAppId: string;
      targetAppId: string;
      interactionType?: string;
      direction?: string;
      businessObject?: string;
      interfaceStatus?: string;
    }) => api.post<any>('/arch-check-interactions', payload),
    onSuccess: () => {
      modals.setAddIntfOpen(false);
      modals.setEditIntfRecord(null);
      modals.setAddIntfForm({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' });
      modals.setAddIntfErrors({});
      modals.setIntfSourceSearchKeyword('');
      modals.setIntfTargetSearchKeyword('');
      messageApi.success('Interaction added successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to add interaction');
    },
  });

  const updateArchCheckInteraction = useMutation({
    mutationFn: (payload: {
      interactionUuid: string;
      sourceAppId: string;
      targetAppId: string;
      interactionType?: string;
      direction?: string;
      businessObject?: string;
      interfaceStatus?: string;
    }) => api.put<any>(`/arch-check-interactions/${payload.interactionUuid}`, payload),
    onSuccess: () => {
      modals.setAddIntfOpen(false);
      modals.setEditIntfRecord(null);
      modals.setAddIntfForm({ sourceAppId: '', applicationName: '', targetAppId: '', targetAppName: '', businessObject: '', integrationType: '', direction: '', changeStatus: '' });
      modals.setAddIntfErrors({});
      modals.setIntfSourceSearchKeyword('');
      modals.setIntfTargetSearchKeyword('');
      messageApi.success('Interaction updated successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to update interaction');
    },
  });

  const deleteArchCheckInteraction = useMutation({
    mutationFn: (interactionUuid: string) => api.delete<any>(`/arch-check-interactions/${interactionUuid}`),
    onSuccess: () => {
      messageApi.success('Interaction deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to delete interaction');
    },
  });

  const confirmArchCheckApps = useMutation({
    mutationFn: (checkAppUuids: React.Key[]) => api.post<any>('/arch-check-apps/confirm', { checkAppUuids }),
    onSuccess: () => {
      messageApi.success('Applications confirmed successfully');
      setAppSelectedKeys([]);
      queryClient.invalidateQueries({ queryKey: ['archCheckApps', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to confirm applications');
    },
  });

  const confirmArchCheckInteractions = useMutation({
    mutationFn: (interactionUuids: React.Key[]) => api.post<any>('/arch-check-interactions/confirm', { interactionUuids }),
    onSuccess: () => {
      messageApi.success('Interactions confirmed successfully');
      setIntfSelectedKeys([]);
      queryClient.invalidateQueries({ queryKey: ['archCheckInteractions', aiDetail?._aiCheckId] });
    },
    onError: () => {
      messageApi.error('Failed to confirm interactions');
    },
  });

  const handleOpenAiDetail = (row: any, bizType: 'App_Arch' | 'Tech_Arch') => {
    setAiDrawerTab('score');
    setAiDetail({
      ...row.aiResult,
      _attachmentId: row.id,
      _fileName: row.fileName,
      _archType: row.appArchType,
      _aiCheckId: row.aiCheckId,
      _bizType: bizType,
    });
  };

  const handleCloseAiDrawer = () => {
    setAiDetail(null);
    setAiDrawerTab('score');
    setAiIssueFilter([]);
    setAppPage(1);
    setAppSelectedKeys([]);
    modals.setAddAppOpen(false);
    setIntfPage(1);
    setIntfSelectedKeys([]);
    modals.setAddIntfOpen(false);
    modals.setEditIntfRecord(null);
    modals.setAddIntfErrors({});
  };

  return {
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
  };
}