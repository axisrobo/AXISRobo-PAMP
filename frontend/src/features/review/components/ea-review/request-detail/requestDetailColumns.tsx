'use client';

import { Button, DatePicker, Input, Popconfirm, Select, Spin, Tooltip } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import { DeleteOutlined, EditOutlined, FileSearchOutlined, SyncOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Column } from '@/shared/components/ui/DataTable';

type DiagramBizType = 'App_Arch' | 'Tech_Arch';

function fmtDateTime(value?: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function buildAttachmentDisplayName(row: any): string {
  const originalName: string = row.originalName || row.fileName || '';
  const createdAt: string = row.createdAt || '';
  if (!originalName) return row.fileName || '-';

  const dotIdx = originalName.lastIndexOf('.');
  const nameWithoutExt = dotIdx > 0 ? originalName.slice(0, dotIdx) : originalName;
  const ext = dotIdx > 0 ? originalName.slice(dotIdx) : '';
  const dtPart = createdAt
    ? new Date(createdAt)
      .toLocaleString('sv-SE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
      .replace(/[-: ]/g, '')
      .replace('T', '')
    : '';

  return dtPart ? `${nameWithoutExt}_${dtPart}${ext}` : originalName;
}

export function createDiagramColumns({
  bizType,
  onOpenAiDetail,
  onDownloadAttachment,
  onRerunAiCheck,
  checkingId,
}: {
  bizType: DiagramBizType;
  onOpenAiDetail: (row: any, bizType: DiagramBizType) => void;
  onDownloadAttachment: (attachmentId: string, fileName: string) => void;
  onRerunAiCheck?: (row: any, bizType: DiagramBizType) => void;
  checkingId?: string | null;
}): Column<any>[] {
  return [
    { key: 'no', title: 'No.', width: 100, render: (_value, _row, index) => (index ?? 0) + 1 },
    {
      key: 'aiScore',
      title: <span>AI Evaluation Score</span>,
      render: (value, row) => {
        if (checkingId === row.id) {
          return (
            <span className="flex items-center gap-1 text-blue-500 text-sm">
              <Spin indicator={<LoadingOutlined style={{ fontSize: 14 }} />} size="small" />
            </span>
          );
        }
        if (value == null) {
          return onRerunAiCheck ? (
            <Tooltip title="Re-run AI check">
              <SyncOutlined
                className="text-gray-400 hover:text-blue-500 cursor-pointer"
                style={{ fontSize: 14 }}
                onClick={() => onRerunAiCheck(row, bizType)}
              />
            </Tooltip>
          ) : '-';
        }
        const score = Number(value);
        const color = score >= 7 ? 'text-green-600' : score >= 4 ? 'text-yellow-600' : 'text-red-600';
        return (
          <div className="flex items-center gap-1.5">
            {row.aiResult && (
              <Button
                type="link"
                size="small"
                icon={<FileSearchOutlined />}
                onClick={() => onOpenAiDetail(row, bizType)}
                title="View AI evaluation detail"
                style={{ padding: 0 }}
              />
            )}
            <span className={`${color} font-bold`}>{value}</span>
            {onRerunAiCheck && (
              <Tooltip title="Re-run AI check">
                <SyncOutlined
                  className="text-gray-400 hover:text-blue-500 cursor-pointer"
                  style={{ fontSize: 12 }}
                  onClick={() => onRerunAiCheck(row, bizType)}
                />
              </Tooltip>
            )}
          </div>
        );
      },
    },
    {
      key: 'fileName',
      title: 'File Name',
      render: (value, row) => value ? (
        <Button type="link" size="small" style={{ padding: 0 }} onClick={() => onDownloadAttachment(row.id, value)}>
          {value}
        </Button>
      ) : '-',
    },
    { key: 'evaluatedAt', title: 'Evaluated At', render: (value) => fmtDateTime(value) },
    { key: 'uploadBy', title: 'Upload By' },
  ];
}

export function createAttachmentColumns({
  canManageAttachments,
  onDownloadAttachment,
  onDeleteAttachment,
}: {
  canManageAttachments: boolean;
  onDownloadAttachment: (attachmentId: string, fileName: string) => void;
  onDeleteAttachment: (attachmentId: string) => void;
}): Column<any>[] {
  return [
    { key: 'no', title: 'No.', render: (_value: any, _row: any, index: any) => (index ?? 0) + 1 },
    {
      key: 'fileName',
      title: 'File Name',
      render: (_value: any, row: any) => {
        const displayName = buildAttachmentDisplayName(row);
        return displayName !== '-'
          ? (
            <Button type="link" size="small" style={{ padding: 0 }} onClick={() => onDownloadAttachment(row.id, displayName)}>
              {displayName}
            </Button>
          )
          : '-';
      },
    },
    { key: 'uploadBy', title: 'Upload By' },
    { key: 'createdAt', title: 'Upload Time', render: (value: any) => fmtDateTime(value) },
    {
      key: 'action',
      title: 'Action',
      render: (_value: any, row: any) => canManageAttachments ? (
        <Popconfirm
          title="Are you sure you want to delete this attachment?"
          okText="Delete"
          okButtonProps={{ danger: true }}
          cancelText="Cancel"
          onConfirm={() => onDeleteAttachment(row.id)}
        >
          <Button type="link" size="small" danger style={{ padding: 0 }} icon={<DeleteOutlined />} />
        </Popconfirm>
      ) : null,
    },
  ];
}