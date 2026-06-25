'use client';

import { useEffect, useRef, useState } from 'react';
import { Button, Modal } from 'antd';
import { CloseOutlined, CompressOutlined, ExpandOutlined } from '@ant-design/icons';
import { TechArchScorePanel } from './TechArchScorePanel';
import { ImageViewerModal } from './modals/ImageViewerModal';

type Props = {
  open: boolean;
  aiDetail: any;
  t: (key: string) => string;
  aiIssueFilter: string[];
  setAiIssueFilter: (vals: string[]) => void;
  onClose: () => void;
};

/** 内容的设计基准宽度（与原 Drawer 1100px 减去左右 padding 20px×2 一致）*/
const DESIGN_WIDTH = 1060;

export function TechArchReportDrawer({
  open,
  aiDetail,
  t,
  aiIssueFilter,
  setAiIssueFilter,
  onClose,
}: Props) {
  const [fullscreen, setFullscreen] = useState(false);
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [scaledHeight, setScaledHeight] = useState<number | undefined>(undefined);
  // Image viewer state lives here so its portal is always after the report modal portal
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerSrc, setViewerSrc] = useState<string | null>(null);

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

  return (
    <>
    <Modal
      open={open}
      onCancel={onClose}
      afterClose={() => { setFullscreen(false); setScale(1); setScaledHeight(undefined); setViewerOpen(false); setViewerSrc(null); }}
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
          <span style={{ fontWeight: 600, fontSize: 15 }}>{t('Technical Architecture AI Check Report')}</span>
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
            <TechArchScorePanel
              aiDetail={aiDetail}
              t={t}
              aiIssueFilter={aiIssueFilter}
              setAiIssueFilter={setAiIssueFilter}
              setViewerSrc={setViewerSrc}
              setViewerOpen={setViewerOpen}
            />
          </div>
        </div>
      )}
    </Modal>
    {/* ImageViewerModal is rendered as a sibling AFTER the report Modal so its portal
        is always appended to document.body after the report modal portal, guaranteeing
        it appears on top regardless of how many times the report is opened/closed. */}
    <ImageViewerModal
      open={viewerOpen}
      viewerSrc={viewerSrc}
      onClose={() => setViewerOpen(false)}
    />
  </>);
}
