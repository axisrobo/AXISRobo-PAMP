'use client';

import { Button, Space } from 'antd';
import { DownloadOutlined, UploadOutlined, PlusOutlined } from '@ant-design/icons';

interface ActionBarProps {
  onExport?: () => void;
  onImport?: () => void;
  onNew?: () => void;
  showExport?: boolean;
  showImport?: boolean;
  showNew?: boolean;
  newLabel?: string;
  children?: React.ReactNode;
}

export function ActionBar({
  onExport,
  onImport,
  onNew,
  showExport = false,
  showImport = false,
  showNew = false,
  newLabel = 'New',
  children,
}: ActionBarProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">{children}</div>
      <Space>
        {showImport && (
          <Button size="small" icon={<UploadOutlined />} onClick={onImport}>
            Import
          </Button>
        )}
        {showExport && (
          <Button size="small" icon={<DownloadOutlined />} onClick={onExport}>
            Export
          </Button>
        )}
        {showNew && (
          <Button type="primary" size="small" icon={<PlusOutlined />} onClick={onNew}>
            {newLabel}
          </Button>
        )}
      </Space>
    </div>
  );
}
