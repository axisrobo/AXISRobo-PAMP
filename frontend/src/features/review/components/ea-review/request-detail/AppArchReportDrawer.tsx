'use client';

import { useEffect, useRef, useState } from 'react';
import { App, Button, Modal, Pagination as AntPagination, Table, Tabs } from 'antd';
import { CloseOutlined, CompressOutlined, ExpandOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { AppArchScorePanel } from './AppArchScorePanel';

/** 内容的设计基准宽度 */
const DESIGN_WIDTH = 1060;

type Props = {
  open: boolean;
  aiDetail: any;
  t: (key: string) => string;
  aiDrawerTab: string;
  setAiDrawerTab: (tab: string) => void;
  aiIssueFilter: string[];
  setAiIssueFilter: (vals: string[]) => void;
  setViewerSrc: (src: string | null) => void;
  setViewerOpen: (open: boolean) => void;
  onClose: () => void;
  archCheckApps?: any[];
  archCheckAppsFetching?: boolean;
  archCheckInteractions?: any[];
  archCheckInteractionsFetching?: boolean;
  appPage: number;
  appPageSize: number;
  setAppPage: (page: number) => void;
  setAppPageSize: (size: number) => void;
  appSelectedKeys: React.Key[];
  setAppSelectedKeys: (keys: React.Key[]) => void;
  confirmArchCheckApps: any;
  deleteArchCheckApp: any;
  onOpenAddApp: () => void;
  onOpenEditApp: (record: any) => void;
  intfPage: number;
  intfPageSize: number;
  setIntfPage: (page: number) => void;
  setIntfPageSize: (size: number) => void;
  intfSelectedKeys: React.Key[];
  setIntfSelectedKeys: (keys: React.Key[]) => void;
  confirmArchCheckInteractions: any;
  deleteArchCheckInteraction: any;
  onOpenAddInterface: () => void;
  onOpenEditInterface: (record: any) => void;
};

export function AppArchReportDrawer({
  open,
  aiDetail,
  t,
  aiDrawerTab,
  setAiDrawerTab,
  aiIssueFilter,
  setAiIssueFilter,
  setViewerSrc,
  setViewerOpen,
  onClose,
  archCheckApps,
  archCheckAppsFetching,
  archCheckInteractions,
  archCheckInteractionsFetching,
  appPage,
  appPageSize,
  setAppPage,
  setAppPageSize,
  appSelectedKeys,
  setAppSelectedKeys,
  confirmArchCheckApps,
  deleteArchCheckApp,
  onOpenAddApp,
  onOpenEditApp,
  intfPage,
  intfPageSize,
  setIntfPage,
  setIntfPageSize,
  intfSelectedKeys,
  setIntfSelectedKeys,
  confirmArchCheckInteractions,
  deleteArchCheckInteraction,
  onOpenAddInterface,
  onOpenEditInterface,
}: Props) {
  const { modal } = App.useApp();
  const [fullscreen, setFullscreen] = useState(false);
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [scaledHeight, setScaledHeight] = useState<number | undefined>(undefined);

  useEffect(() => {
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;
    const update = () => {
      const w = outer.clientWidth;
      const s = w > 0 ? Math.min(w / DESIGN_WIDTH, 1) : 1;
      setScale(s);
      setScaledHeight(inner.scrollHeight * s);
    };
    const ro = new ResizeObserver(update);
    ro.observe(outer);
    ro.observe(inner);
    update();
    return () => ro.disconnect();
  }, [open, fullscreen]);

  const contentExtract = (aiDetail as any)?.content_extract_result ?? {};
  const extractedApps: any[] = Array.isArray(contentExtract?.applications) ? contentExtract.applications : [];
  const apps: any[] = (archCheckApps && archCheckApps.length > 0)
    ? archCheckApps
    : extractedApps.map((app: any) => ({
        appId: app?.id ?? '',
        appName: app?.name ?? '',
        appClassification: app?.id_is_standard ? 'Standard' : 'Non-standard',
        bizFunction: Array.isArray(app?.functions) ? app.functions.join(', ') : '',
        appSolutionOwnerName: '',
        checkAppStatus: app?.application_status ?? '',
        confirmStatus: t('Waiting to Confirm'),
      }));

  const pageData = apps.slice((appPage - 1) * appPageSize, appPage * appPageSize);
  const intfs: any[] = archCheckInteractions ?? [];
  const intfPageData = intfs.slice((intfPage - 1) * intfPageSize, intfPage * intfPageSize);

  const appColumns = [
    { title: t('Application ID'), dataIndex: 'appId', key: 'appId', width: 130 },
    { title: t('Application Name'), dataIndex: 'appName', key: 'appName', width: 150,
      render: (v: string) => <span className="block max-w-[130px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Application Classification'), dataIndex: 'appClassification', key: 'appClassification', width: 160,
      render: (v: string) => <span className="block max-w-[140px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Value Chain'), dataIndex: 'bizFunction', key: 'bizFunction', width: 130,
      render: (v: string) => <span className="block max-w-[110px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Solution Owner'), dataIndex: 'appSolutionOwnerName', key: 'appSolutionOwnerName', width: 130 },
    { title: t('Check App Status'), dataIndex: 'checkAppStatus', key: 'checkAppStatus', width: 120,
      render: (v: string) => <span className="block max-w-[100px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Operated By'), dataIndex: 'statusChangedByName', key: 'statusChangedByName', width: 120,
      render: (v: string) => <span>{v ?? '-'}</span> },
    { title: t('Operated At'), dataIndex: 'statusChangedAt', key: 'statusChangedAt', width: 150,
      render: (v: string) => v ? <span>{dayjs(v).format('YYYY-MM-DD HH:mm')}</span> : <span>-</span> },
    { title: t('EA Comments'), dataIndex: 'remark', key: 'remark', width: 160,
      render: (v: string) => <span className="block max-w-[140px] truncate" title={v ?? ''}>{v ?? '-'}</span> },
    { title: t('Confirm Status'), dataIndex: 'confirmStatus', key: 'confirmStatus', width: 150, fixed: 'right' as const,
      render: (v: string) => <span className="text-text-secondary text-sm">{v ?? t('Waiting to Confirm')}</span> },
    { title: t('Operation'), key: 'operation', width: 80, fixed: 'right' as const,
      render: (_: any, record: any) => (
        <div className="flex items-center gap-2">
          <Button type="link" size="small" style={{ padding: 0, color: '#3b82f6' }} icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          } onClick={() => onOpenEditApp(record)} />
          <Button type="link" size="small" style={{ padding: 0, color: '#ef4444' }} loading={deleteArchCheckApp.isPending && deleteArchCheckApp.variables === record.checkAppUuid} icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          } onClick={() => {
            modal.confirm({
              title: t('Are you sure you want to delete this application?'),
              okText: t('Delete'),
              okButtonProps: { danger: true },
              cancelText: t('Cancel'),
              onOk: () => deleteArchCheckApp.mutate(record.checkAppUuid),
            });
          }} />
        </div>
      ),
    },
  ];

  const intfColumns = [
    { title: t('Source App ID'), dataIndex: 'sourceAppId', key: 'sourceAppId', width: 120 },
    { title: t('Source App Name'), dataIndex: 'sourceAppName', key: 'sourceAppName', width: 140,
      render: (v: string) => <span className="block max-w-[120px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Target App ID'), dataIndex: 'targetAppId', key: 'targetAppId', width: 120 },
    { title: t('Target App Name'), dataIndex: 'targetAppName', key: 'targetAppName', width: 140,
      render: (v: string) => <span className="block max-w-[120px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Business Object'), dataIndex: 'businessObject', key: 'businessObject', width: 140,
      render: (v: string) => <span className="block max-w-[120px] truncate" title={v}>{v ?? '-'}</span> },
    { title: t('Interaction Type'), dataIndex: 'interactionType', key: 'interactionType', width: 130,
      render: (v: string) => <span className="text-sm">{v ?? '-'}</span> },
    { title: t('Direction'), dataIndex: 'direction', key: 'direction', width: 100,
      render: (v: string) => <span className="text-sm">{v ?? '-'}</span> },
    { title: t('Change Status'), dataIndex: 'interfaceStatus', key: 'interfaceStatus', width: 120,
      render: (v: string) => <span className="text-sm">{v ?? '-'}</span> },
    { title: t('Operated By'), dataIndex: 'statusChangedByName', key: 'statusChangedByName', width: 120,
      render: (v: string) => <span className="text-sm">{v ?? '-'}</span> },
    { title: t('Operated At'), dataIndex: 'statusChangedAt', key: 'statusChangedAt', width: 160,
      render: (v: string) => <span className="text-sm">{v ? new Date(v).toLocaleString() : '-'}</span> },
    { title: t('Confirm Status'), dataIndex: 'confirmStatus', key: 'confirmStatus', width: 150, fixed: 'right' as const,
      render: (v: string) => <span className="text-text-secondary text-sm">{v ?? t('Waiting to Confirm')}</span> },
    { title: t('Operation'), key: 'operation', width: 80, fixed: 'right' as const,
      render: (_: any, record: any) => (
        <div className="flex items-center gap-2">
          <Button type="link" size="small" style={{ padding: 0, color: '#3b82f6' }} icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          } onClick={() => onOpenEditInterface(record)} />
          <Button type="link" size="small" style={{ padding: 0, color: '#3b82f6' }} icon={
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          } onClick={() => {
            modal.confirm({
              title: t('Delete Interaction'),
              content: t('Are you sure you want to delete this interaction?'),
              okText: t('Delete'),
              okButtonProps: { danger: true },
              cancelText: t('Cancel'),
              onOk: () => deleteArchCheckInteraction.mutate(record.checkAppUuid),
            });
          }} />
        </div>
      ),
    },
  ];

  return (
    <Modal
      open={open}
      onCancel={onClose}
      afterClose={() => { setFullscreen(false); setScale(1); setScaledHeight(undefined); }}
      footer={null}
      closable={false}
      width={fullscreen ? '100vw' : '70%'}
      style={
        fullscreen
          ? { top: 0, paddingBottom: 0, margin: 0, maxWidth: '100vw' }
          : { top: '5vh' }
      }
      styles={{
        root: fullscreen
          ? { height: '100vh', borderRadius: 0, display: 'flex', flexDirection: 'column', padding: 0 }
          : { padding: 0 },
        header: { padding: '12px 20px', marginBottom: 0, borderBottom: '1px solid #f0f0f0', flexShrink: 0 },
        body: {
          overflow: 'auto',
          flex: fullscreen ? 1 : undefined,
          minHeight: fullscreen ? 0 : undefined,
          maxHeight: fullscreen ? undefined : '78vh',
          padding: '16px 20px',
        },
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 600, fontSize: 15 }}>{t('Application Architecture Diagram AI Check Report')}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Button
              type="text"
              size="small"
              icon={fullscreen ? <CompressOutlined /> : <ExpandOutlined />}
              onClick={() => setFullscreen((f) => !f)}
            />
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={onClose}
            />
          </div>
        </div>
      }
    >
      {aiDetail && (
        <div
          ref={outerRef}
          style={scale < 1 ? { overflow: 'hidden', height: scaledHeight } : {}}
        >
          <div
            ref={innerRef}
            style={{
              transform: scale < 1 ? `scale(${scale})` : undefined,
              transformOrigin: 'top left',
              width: scale < 1 ? DESIGN_WIDTH : undefined,
            }}
          >
        <Tabs
          activeKey={aiDrawerTab}
          onChange={setAiDrawerTab}
          items={[
            {
              key: 'score',
              label: t('AI Evaluation Score'),
              children: (
                <AppArchScorePanel
                  aiDetail={aiDetail}
                  t={t}
                  aiIssueFilter={aiIssueFilter}
                  setAiIssueFilter={setAiIssueFilter}
                  setViewerSrc={setViewerSrc}
                  setViewerOpen={setViewerOpen}
                />
              ),
            },
            {
              key: 'applications',
              label: t('Applications'),
              children: (
                <div className="flex flex-col h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <Button
                      type="primary"
                      icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }}><polyline points="20 6 9 17 4 12"/></svg>}
                      disabled={appSelectedKeys.length === 0}
                      loading={confirmArchCheckApps.isPending}
                      onClick={() => {
                        modal.confirm({
                          title: t('Confirm Applications'),
                          content: t('Are you sure you want to confirm these application items?'),
                          okText: t('OK'),
                          cancelText: t('Cancel'),
                          icon: null,
                          onOk: () => confirmArchCheckApps.mutateAsync(appSelectedKeys),
                        });
                      }}
                    >
                      {t('Confirm')}
                    </Button>
                    <Button
                      icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>}
                      onClick={onOpenAddApp}
                    >
                      {t('Add')}
                    </Button>
                  </div>
                  <Table
                    size="small"
                    rowSelection={{
                      selectedRowKeys: appSelectedKeys,
                      onChange: setAppSelectedKeys,
                      fixed: true,
                      getCheckboxProps: (record: any) => ({
                        disabled: record.confirmStatus === 'Confirmed',
                        style: record.confirmStatus === 'Confirmed' ? { display: 'none' } : undefined,
                      }),
                    }}
                    columns={appColumns}
                    dataSource={pageData}
                    rowKey={(r: any) => r.checkAppUuid ?? r.appId ?? Math.random()}
                    pagination={false}
                    loading={archCheckAppsFetching}
                    scroll={{ x: 'max-content' }}
                    locale={{ emptyText: <div className="py-8 text-center text-text-secondary text-sm">{t('No applications')}</div> }}
                  />
                  {apps.length > 0 && (
                    <div className="flex justify-end mt-3">
                      <AntPagination
                        current={appPage}
                        pageSize={appPageSize}
                        total={apps.length}
                        showTotal={(total) => `${t('Total')} ${total} ${t('items')}`}
                        showSizeChanger
                        pageSizeOptions={['10', '20', '50']}
                        onChange={(p, ps) => { setAppPage(p); setAppPageSize(ps); }}
                        size="small"
                      />
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: 'interfaces',
              label: t('Interfaces'),
              children: (
                <div className="flex flex-col h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <Button
                      type="primary"
                      icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }}><polyline points="20 6 9 17 4 12"/></svg>}
                      disabled={intfSelectedKeys.length === 0}
                      loading={confirmArchCheckInteractions.isPending}
                      onClick={() => {
                        modal.confirm({
                          title: t('Confirm Interfaces'),
                          content: t('Are you sure you want to confirm these interface items?'),
                          okText: t('OK'),
                          cancelText: t('Cancel'),
                          onOk: () => confirmArchCheckInteractions.mutate(intfSelectedKeys),
                        });
                      }}
                    >
                      {t('Confirm')}
                    </Button>
                    <Button
                      icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>}
                      onClick={onOpenAddInterface}
                    >
                      {t('Add')}
                    </Button>
                  </div>
                  <Table
                    size="small"
                    rowSelection={{
                      selectedRowKeys: intfSelectedKeys,
                      onChange: setIntfSelectedKeys,
                      fixed: true,
                      getCheckboxProps: (record: any) => ({
                        disabled: record.confirmStatus === 'Confirmed',
                        style: record.confirmStatus === 'Confirmed' ? { display: 'none' } : undefined,
                      }),
                    }}
                    columns={intfColumns}
                    dataSource={intfPageData}
                    rowKey={(r: any) => r.checkAppUuid ?? `${r.sourceAppId}-${r.targetAppId}-${r.businessObject}`}
                    pagination={false}
                    loading={archCheckInteractionsFetching}
                    scroll={{ x: 'max-content' }}
                    locale={{ emptyText: <div className="py-8 text-center text-text-secondary text-sm">{t('No interfaces')}</div> }}
                  />
                  {intfs.length > 0 && (
                    <div className="flex justify-end mt-3">
                      <AntPagination
                        current={intfPage}
                        pageSize={intfPageSize}
                        total={intfs.length}
                        showTotal={(total) => `${t('Total')} ${total} ${t('items')}`}
                        showSizeChanger
                        pageSizeOptions={['10', '20', '50']}
                        onChange={(p, ps) => { setIntfPage(p); setIntfPageSize(ps); }}
                        size="small"
                      />
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
          </div>
        </div>
      )}
    </Modal>
  );
}
