'use client';

import type { Dispatch, SetStateAction } from 'react';
import { Button, Input, Modal, Select } from 'antd';

type IntfForm = {
  sourceAppId: string;
  applicationName: string;
  targetAppId: string;
  targetAppName: string;
  businessObject: string;
  integrationType: string;
  direction: string;
  changeStatus: string;
};

type IntfErrors = {
  sourceAppId?: string;
  targetAppId?: string;
  changeStatus?: string;
};

type Props = {
  open: boolean;
  editIntfRecord: any;
  t: (key: string) => string;
  addIntfForm: IntfForm;
  setAddIntfForm: Dispatch<SetStateAction<IntfForm>>;
  addIntfErrors: IntfErrors;
  setAddIntfErrors: Dispatch<SetStateAction<IntfErrors>>;
  intfSourceFetching: boolean;
  intfTargetFetching: boolean;
  intfSourceApps: any;
  intfTargetApps: any;
  setIntfSourceSearchKeyword: (val: string) => void;
  setIntfTargetSearchKeyword: (val: string) => void;
  saveLoading: boolean;
  onCancel: () => void;
  onSave: () => void;
};

export function AddInterfaceModal({
  open,
  editIntfRecord,
  t,
  addIntfForm,
  setAddIntfForm,
  addIntfErrors,
  setAddIntfErrors,
  intfSourceFetching,
  intfTargetFetching,
  intfSourceApps,
  intfTargetApps,
  setIntfSourceSearchKeyword,
  setIntfTargetSearchKeyword,
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
      title={editIntfRecord ? t('Edit Interface') : t('Add Interface')}
      styles={{ body: { padding: '32px 32px 24px' } }}
    >
      <div className="grid grid-cols-2 gap-x-8 gap-y-5">
        <div className="space-y-4">
          <div>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-red-500 text-sm">*</span>
              <label className="text-sm text-text-secondary">{t('Source App ID')}</label>
            </div>
            <Select
              showSearch
              filterOption={false}
              style={{ width: '100%' }}
              placeholder={t('Search by App ID or Name')}
              value={addIntfForm.sourceAppId || undefined}
              status={addIntfErrors.sourceAppId ? 'error' : undefined}
              loading={intfSourceFetching}
              onSearch={(val) => setIntfSourceSearchKeyword(val)}
              onChange={(val) => {
                const hit = (intfSourceApps?.data ?? []).find((r: any) => r.appId === val);
                setAddIntfForm((f) => ({
                  ...f,
                  sourceAppId: val,
                  applicationName: hit?.name ?? hit?.appFullName ?? '',
                }));
                setAddIntfErrors((e) => ({ ...e, sourceAppId: undefined }));
              }}
              options={[
                ...(addIntfForm.sourceAppId && !(intfSourceApps?.data ?? []).find((r: any) => r.appId === addIntfForm.sourceAppId)
                  ? [{ value: addIntfForm.sourceAppId, label: `${addIntfForm.sourceAppId} - ${addIntfForm.applicationName || ''}` }]
                  : []),
                ...(intfSourceApps?.data ?? []).map((r: any) => ({
                  value: r.appId,
                  label: `${r.appId} - ${r.name || r.appFullName || ''}`,
                })),
              ]}
              notFoundContent={intfSourceFetching ? t('Loading...') : t('No results')}
            />
            {addIntfErrors.sourceAppId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Source App Name')}</label>
            <Input value={addIntfForm.applicationName ?? ''} readOnly className="bg-gray-100" />
          </div>

          <div>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-red-500 text-sm">*</span>
              <label className="text-sm text-text-secondary">{t('Target App ID')}</label>
            </div>
            <Select
              showSearch
              filterOption={false}
              style={{ width: '100%' }}
              placeholder={t('Search by App ID or Name')}
              value={addIntfForm.targetAppId || undefined}
              status={addIntfErrors.targetAppId ? 'error' : undefined}
              loading={intfTargetFetching}
              onSearch={(val) => setIntfTargetSearchKeyword(val)}
              onChange={(val) => {
                const hit = (intfTargetApps?.data ?? []).find((r: any) => r.appId === val);
                setAddIntfForm((f) => ({
                  ...f,
                  targetAppId: val,
                  targetAppName: hit?.name ?? hit?.appFullName ?? '',
                }));
                setAddIntfErrors((e) => ({ ...e, targetAppId: undefined }));
              }}
              options={[
                ...(addIntfForm.targetAppId && !(intfTargetApps?.data ?? []).find((r: any) => r.appId === addIntfForm.targetAppId)
                  ? [{ value: addIntfForm.targetAppId, label: `${addIntfForm.targetAppId} - ${addIntfForm.targetAppName || ''}` }]
                  : []),
                ...(intfTargetApps?.data ?? []).map((r: any) => ({
                  value: r.appId,
                  label: `${r.appId} - ${r.name || r.appFullName || ''}`,
                })),
              ]}
              notFoundContent={intfTargetFetching ? t('Loading...') : t('No results')}
            />
            {addIntfErrors.targetAppId && <div className="text-red-500 text-xs mt-0.5">Required</div>}
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Target App Name')}</label>
            <Input value={addIntfForm.targetAppName ?? ''} readOnly className="bg-gray-100" />
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Business Object')}</label>
            <Input value={addIntfForm.businessObject} onChange={(e) => setAddIntfForm((f) => ({ ...f, businessObject: e.target.value }))} />
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Interaction Type')}</label>
            <Select
              style={{ width: '100%' }}
              placeholder=""
              value={addIntfForm.integrationType || undefined}
              onChange={(val) => setAddIntfForm((f) => ({ ...f, integrationType: val }))}
              options={[
                { value: 'Command', label: 'Command' },
                { value: 'Event', label: 'Event' },
                { value: 'Query', label: 'Query' },
                { value: 'Embed', label: 'Embed' },
              ]}
            />
          </div>

          <div>
            <label className="text-sm text-text-secondary block mb-1">{t('Direction')}</label>
            <Input value={addIntfForm.direction ?? ''} onChange={(e) => setAddIntfForm((f) => ({ ...f, direction: e.target.value }))} />
          </div>

          <div>
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-red-500 text-sm">*</span>
              <label className="text-sm text-text-secondary">{t('Change Status')}</label>
            </div>
            <Select
              style={{ width: '100%' }}
              placeholder=""
              value={addIntfForm.changeStatus || undefined}
              status={addIntfErrors.changeStatus ? 'error' : undefined}
              onChange={(val) => setAddIntfForm((f) => ({ ...f, changeStatus: val }))}
              options={[
                { value: 'New', label: 'New' },
                { value: 'Keep', label: 'Keep' },
                { value: 'Change', label: 'Change' },
                { value: 'Sunset', label: 'Sunset' },
                { value: '3rd Party', label: '3rd Party' },
              ]}
            />
            {addIntfErrors.changeStatus && <div className="text-red-500 text-xs mt-0.5">Required</div>}
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
