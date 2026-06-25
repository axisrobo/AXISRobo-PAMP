'use client';

import type { Dispatch, SetStateAction } from 'react';
import { Button, Input, Modal, Select } from 'antd';

type AppForm = {
  applicationId: string;
  applicationName: string;
  applicationClassification: string;
  valueChain: string;
  solutionOwner: string;
  changeStatus: string;
  eaComments: string;
};

type AppErrors = {
  applicationId?: string;
  changeStatus?: string;
};

type Props = {
  open: boolean;
  editAppRecord: any;
  t: (key: string) => string;
  addAppForm: AppForm;
  setAddAppForm: Dispatch<SetStateAction<AppForm>>;
  addAppErrors: AppErrors;
  setAddAppErrors: Dispatch<SetStateAction<AppErrors>>;
  cmdbFetching: boolean;
  cmdbApps: any;
  setAppSearchKeyword: (val: string) => void;
  saveLoading: boolean;
  onCancel: () => void;
  onSave: () => void;
};

export function AddApplicationModal({
  open,
  editAppRecord,
  t,
  addAppForm,
  setAddAppForm,
  addAppErrors,
  setAddAppErrors,
  cmdbFetching,
  cmdbApps,
  setAppSearchKeyword,
  saveLoading,
  onCancel,
  onSave,
}: Props) {
  return (
    <Modal
      open={open}
      onCancel={onCancel}
      footer={null}
      width={760}
      closable
      title={editAppRecord ? t('Edit Application') : t('Add Application')}
      styles={{ body: { padding: '24px 32px 24px' } }}
    >
      <div className="grid grid-cols-2 gap-x-8 gap-y-5">
        <div className="space-y-4">
          <div>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-red-500 text-sm">*</span>
              <label className="text-sm text-text-secondary">{t('Application ID')}</label>
            </div>
            <Select
              showSearch
              filterOption={false}
              style={{ width: '100%' }}
              placeholder={t('Search by App ID or Name')}
              value={addAppForm.applicationId || undefined}
              status={addAppErrors.applicationId ? 'error' : undefined}
              loading={cmdbFetching}
              onSearch={(val) => setAppSearchKeyword(val)}
              onChange={(val) => {
                const hit = (cmdbApps?.data ?? []).find((r: any) => r.appId === val);
                setAddAppForm((f) => ({
                  ...f,
                  applicationId: val,
                  applicationName: hit?.name ?? hit?.appFullName ?? '',
                  applicationClassification: hit?.appClassification ?? '',
                  valueChain: hit?.serviceArea ?? '',
                  solutionOwner: hit?.ownedBy ?? '',
                }));
                setAddAppErrors((e) => ({ ...e, applicationId: undefined }));
              }}
              options={[
                ...(addAppForm.applicationId && !(cmdbApps?.data ?? []).find((r: any) => r.appId === addAppForm.applicationId)
                  ? [{ value: addAppForm.applicationId, label: `${addAppForm.applicationId} - ${addAppForm.applicationName || ''}` }]
                  : []),
                ...(cmdbApps?.data ?? []).map((r: any) => ({
                  value: r.appId,
                  label: `${r.appId} - ${r.name || r.appFullName || ''}`,
                })),
              ]}
              notFoundContent={cmdbFetching ? t('Loading...') : t('No results')}
            />
            {addAppErrors.applicationId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Application Name')}</label>
            <Input
              value={addAppForm.applicationName}
              onChange={(e) => setAddAppForm((f) => ({ ...f, applicationName: e.target.value }))}
              placeholder={t('Application Name')}
            />
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Application Classification')}</label>
            <Input value={addAppForm.applicationClassification} readOnly className="bg-gray-100" />
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Value Chain')}</label>
            <Input value={addAppForm.valueChain} readOnly className="bg-gray-100" />
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Solution Owner')}</label>
            <Input value={addAppForm.solutionOwner} readOnly className="bg-gray-100" />
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-red-500 text-sm">*</span>
              <label className="text-sm text-text-secondary">{t('Check App Status')}</label>
            </div>
            <Select
              style={{ width: '100%' }}
              placeholder=""
              value={addAppForm.changeStatus || undefined}
              status={addAppErrors.changeStatus ? 'error' : undefined}
              onChange={(val) => setAddAppForm((f) => ({ ...f, changeStatus: val }))}
              options={[
                { value: 'New', label: 'New' },
                { value: 'Keep', label: 'Keep' },
                { value: 'Change', label: 'Change' },
                { value: 'Sunset', label: 'Sunset' },
                { value: '3rd Party', label: '3rd Party' },
              ]}
            />
            {addAppErrors.changeStatus && <div className="text-red-500 text-xs mt-0.5">Required</div>}
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Remark')}</label>
            <Input.TextArea
              rows={4}
              value={addAppForm.eaComments}
              onChange={(e) => setAddAppForm((f) => ({ ...f, eaComments: e.target.value }))}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 mt-6">
        <Button onClick={onCancel}>{t('Cancel')}</Button>
        <Button type="primary" loading={saveLoading} onClick={onSave}>{t('Save')}</Button>
      </div>
    </Modal>
  );
}
