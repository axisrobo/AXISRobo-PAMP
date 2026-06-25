'use client';

import { useState } from 'react';

export type AppFormState = {
  applicationId: string;
  applicationName: string;
  applicationClassification: string;
  valueChain: string;
  solutionOwner: string;
  changeStatus: string;
  eaComments: string;
};

export type AppFormErrors = {
  applicationId?: string;
  changeStatus?: string;
};

export type IntfFormState = {
  sourceAppId: string;
  applicationName: string;
  targetAppId: string;
  targetAppName: string;
  businessObject: string;
  integrationType: string;
  direction: string;
  changeStatus: string;
};

export type IntfFormErrors = {
  sourceAppId?: string;
  targetAppId?: string;
  changeStatus?: string;
};

const EMPTY_APP_FORM: AppFormState = {
  applicationId: '',
  applicationName: '',
  applicationClassification: '',
  valueChain: '',
  solutionOwner: '',
  changeStatus: '',
  eaComments: '',
};

const EMPTY_INTF_FORM: IntfFormState = {
  sourceAppId: '',
  applicationName: '',
  targetAppId: '',
  targetAppName: '',
  businessObject: '',
  integrationType: '',
  direction: '',
  changeStatus: '',
};

export function useArchCheckModals() {
  const [addAppOpen, setAddAppOpen] = useState(false);
  const [editAppRecord, setEditAppRecord] = useState<any>(null);
  const [addAppForm, setAddAppForm] = useState<AppFormState>(EMPTY_APP_FORM);
  const [addAppErrors, setAddAppErrors] = useState<AppFormErrors>({});
  const [appSearchKeyword, setAppSearchKeyword] = useState('');

  const [addIntfOpen, setAddIntfOpen] = useState(false);
  const [editIntfRecord, setEditIntfRecord] = useState<any>(null);
  const [addIntfForm, setAddIntfForm] = useState<IntfFormState>(EMPTY_INTF_FORM);
  const [addIntfErrors, setAddIntfErrors] = useState<IntfFormErrors>({});
  const [intfSourceSearchKeyword, setIntfSourceSearchKeyword] = useState('');
  const [intfTargetSearchKeyword, setIntfTargetSearchKeyword] = useState('');

  const openAddApp = () => {
    setEditAppRecord(null);
    setAddAppForm(EMPTY_APP_FORM);
    setAddAppErrors({});
    setAppSearchKeyword('');
    setAddAppOpen(true);
  };

  const openEditApp = (record: any) => {
    setEditAppRecord(record);
    setAddAppForm({
      applicationId: record.appId ?? '',
      applicationName: record.appName ?? '',
      applicationClassification: record.appClassification ?? '',
      valueChain: record.bizFunction ?? '',
      solutionOwner: record.appSolutionOwnerName ?? record.appSolutionOwner ?? '',
      changeStatus: record.checkAppStatus ?? '',
      eaComments: record.remark ?? '',
    });
    setAddAppErrors({});
    setAppSearchKeyword('');
    setAddAppOpen(true);
  };

  const closeAppModal = () => {
    setAddAppOpen(false);
    setEditAppRecord(null);
    setAppSearchKeyword('');
  };

  const saveAppModal = (
    aiCheckId: string | undefined,
    updateArchCheckApp: any,
    addArchCheckApp: any,
  ) => {
    const errors: AppFormErrors = {};
    if (!addAppForm.applicationId) errors.applicationId = 'Required';
    if (!addAppForm.changeStatus) errors.changeStatus = 'Required';
    if (Object.keys(errors).length > 0) {
      setAddAppErrors(errors);
      return;
    }

    if (editAppRecord) {
      updateArchCheckApp.mutate({
        checkAppUuid: editAppRecord.checkAppUuid,
        appId: addAppForm.applicationId,
        appName: addAppForm.applicationName,
        idIsStandard: false,
        checkAppStatus: addAppForm.changeStatus,
        remark: addAppForm.eaComments || undefined,
      });
      return;
    }

    addArchCheckApp.mutate({
      aiCheckId,
      appId: addAppForm.applicationId,
      appName: addAppForm.applicationName,
      idIsStandard: false,
      checkAppStatus: addAppForm.changeStatus,
      remark: addAppForm.eaComments || undefined,
    });
  };

  const openAddInterface = () => {
    setAddIntfForm(EMPTY_INTF_FORM);
    setAddIntfErrors({});
    setAddIntfOpen(true);
  };

  const openEditInterface = (record: any) => {
    setEditIntfRecord(record);
    setAddIntfForm({
      sourceAppId: record.sourceAppId ?? '',
      applicationName: record.sourceAppName ?? '',
      targetAppId: record.targetAppId ?? '',
      targetAppName: record.targetAppName ?? '',
      businessObject: record.businessObject ?? '',
      integrationType: record.interactionType ?? '',
      direction: record.direction ?? '',
      changeStatus: record.interfaceStatus ?? '',
    });
    setAddIntfErrors({});
    setAddIntfOpen(true);
  };

  const closeInterfaceModal = () => {
    setAddIntfOpen(false);
    setEditIntfRecord(null);
    setAddIntfForm(EMPTY_INTF_FORM);
    setAddIntfErrors({});
    setIntfSourceSearchKeyword('');
    setIntfTargetSearchKeyword('');
  };

  const saveInterfaceModal = (
    aiCheckId: string | undefined,
    updateArchCheckInteraction: any,
    addArchCheckInteraction: any,
  ) => {
    const errors: IntfFormErrors = {};
    if (!addIntfForm.sourceAppId) errors.sourceAppId = 'Required';
    if (!addIntfForm.targetAppId) errors.targetAppId = 'Required';
    if (!addIntfForm.changeStatus) errors.changeStatus = 'Required';
    if (Object.keys(errors).length > 0) {
      setAddIntfErrors(errors);
      return;
    }

    if (editIntfRecord) {
      updateArchCheckInteraction.mutate({
        interactionUuid: editIntfRecord.checkAppUuid,
        sourceAppId: addIntfForm.sourceAppId,
        targetAppId: addIntfForm.targetAppId,
        interactionType: addIntfForm.integrationType || undefined,
        direction: addIntfForm.direction || undefined,
        businessObject: addIntfForm.businessObject || undefined,
        interfaceStatus: addIntfForm.changeStatus || undefined,
      });
      return;
    }

    addArchCheckInteraction.mutate({
      aiCheckId,
      sourceAppId: addIntfForm.sourceAppId,
      targetAppId: addIntfForm.targetAppId,
      interactionType: addIntfForm.integrationType || undefined,
      direction: addIntfForm.direction || undefined,
      businessObject: addIntfForm.businessObject || undefined,
      interfaceStatus: addIntfForm.changeStatus || undefined,
    });
  };

  return {
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
  };
}
