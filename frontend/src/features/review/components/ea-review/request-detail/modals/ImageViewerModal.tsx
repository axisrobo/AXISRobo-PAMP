'use client';

import { useEffect, useState } from 'react';
import { Button, Modal, Tooltip } from 'antd';
import {
  CloseOutlined,
  CompressOutlined,
  ExpandOutlined,
  MinusOutlined,
  PlusOutlined,
  RedoOutlined,
} from '@ant-design/icons';

type Props = {
  open: boolean;
  viewerSrc: string | null;
  onClose: () => void;
};

const MIN_SCALE = 0.5;
const MAX_SCALE = 3;
const SCALE_STEP = 0.25;

export function ImageViewerModal({ open, viewerSrc, onClose }: Props) {
  const [fullscreen, setFullscreen] = useState(false);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    if (!open) {
      setFullscreen(false);
      setScale(1);
    }
  }, [open]);

  const zoomOutDisabled = scale <= MIN_SCALE;
  const zoomInDisabled = scale >= MAX_SCALE;

  return (
    <Modal
      open={open}
      onCancel={onClose}
      afterClose={() => {
        setFullscreen(false);
        setScale(1);
      }}
      footer={null}
      closable={false}
      width={fullscreen ? '100vw' : 960}
      style={fullscreen ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : { top: 24 }}
      styles={{
        header: {
          padding: '12px 16px',
          marginBottom: 0,
          borderBottom: '1px solid #f0f0f0',
        },
        body: {
          padding: 0,
          height: fullscreen ? 'calc(100vh - 57px)' : '72vh',
          backgroundColor: '#f8fafc',
        },
        mask: { backgroundColor: 'rgba(0,0,0,0.4)' },
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <span style={{ fontWeight: 600, fontSize: 15 }}>Diagram Preview</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ minWidth: 48, textAlign: 'center', fontSize: 12, color: '#6b7280' }}>
              {Math.round(scale * 100)}%
            </span>
            <Tooltip title="Zoom out">
              <Button
                type="text"
                size="small"
                icon={<MinusOutlined />}
                disabled={zoomOutDisabled}
                onClick={() => setScale((current) => Math.max(MIN_SCALE, current - SCALE_STEP))}
              />
            </Tooltip>
            <Tooltip title="Reset size">
              <Button
                type="text"
                size="small"
                icon={<RedoOutlined />}
                onClick={() => setScale(1)}
              />
            </Tooltip>
            <Tooltip title="Zoom in">
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined />}
                disabled={zoomInDisabled}
                onClick={() => setScale((current) => Math.min(MAX_SCALE, current + SCALE_STEP))}
              />
            </Tooltip>
            <Tooltip title={fullscreen ? 'Exit fullscreen' : 'Maximize'}>
              <Button
                type="text"
                size="small"
                icon={fullscreen ? <CompressOutlined /> : <ExpandOutlined />}
                onClick={() => setFullscreen((current) => !current)}
              />
            </Tooltip>
            <Tooltip title="Close">
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={onClose}
              />
            </Tooltip>
          </div>
        </div>
      }
    >
      <div
        style={{
          width: '100%',
          height: '100%',
          overflow: 'auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
        }}
      >
        {viewerSrc && (
          <img
            src={viewerSrc}
            alt="Diagram Preview"
            style={{
              display: 'block',
              maxWidth: fullscreen ? '90vw' : 'min(70vw, 720px)',
              maxHeight: fullscreen ? '88vh' : 'min(60vh, 520px)',
              width: 'auto',
              height: 'auto',
              objectFit: 'contain',
              transform: `scale(${scale})`,
              transformOrigin: 'center center',
              transition: 'transform 0.2s ease',
              backgroundColor: '#fff',
              boxShadow: '0 10px 30px rgba(15, 23, 42, 0.12)',
            }}
          />
        )}
      </div>
    </Modal>
  );
}
