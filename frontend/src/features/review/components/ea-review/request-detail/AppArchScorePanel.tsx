'use client';

import { useEffect, useRef, useState } from 'react';
import { InfoCircleOutlined } from '@ant-design/icons';
import { Select } from 'antd';
import { formatAiScoreDimensionLabel, getAiOverallScore } from '@/shared/lib/ai-review';
import { getAuthToken } from '@/shared/lib/auth-token';

type Props = {
  aiDetail: any;
  t: (key: string) => string;
  aiIssueFilter: string[];
  setAiIssueFilter: (vals: string[]) => void;
  setViewerSrc: (src: string | null) => void;
  setViewerOpen: (open: boolean) => void;
};

function AuthenticatedImage({
  src,
  alt,
  className,
  style,
  onClick,
}: {
  src: string;
  alt: string;
  className?: string;
  style?: React.CSSProperties;
  onClick?: (blobUrl: string | null) => void;
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    let objectUrl: string;
    const token = getAuthToken();
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch(src, { headers })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      })
      .catch(() => setErrored(true));
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src]);

  if (errored) return <div className="text-xs text-text-secondary p-2">Image failed to load</div>;
  if (!blobUrl) return <div className="flex items-center justify-center h-24 text-xs text-text-secondary">Loading...</div>;

  return (
    <img
      src={blobUrl}
      alt={alt}
      style={style}
      className={`${className ?? ''} cursor-pointer`}
      onClick={() => onClick?.(blobUrl)}
    />
  );
}

export function AppArchScorePanel({
  aiDetail,
  t,
  aiIssueFilter,
  setAiIssueFilter,
  setViewerSrc,
  setViewerOpen,
}: Props) {
  const scoreData = aiDetail?.score_breakdown || {};
  const scoreEntries = Object.entries(scoreData) as [string, number][];
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '/api';

  const radarSize = 240;
  const cx = radarSize / 2;
  const cy = radarSize / 2;
  const radius = radarSize / 2 - 40;
  const N = scoreEntries.length;
  const angleStep = N > 0 ? (2 * Math.PI) / N : 0;

  function polarX(i: number, r: number) {
    return cx + r * Math.sin(i * angleStep);
  }
  function polarY(i: number, r: number) {
    return cy - r * Math.cos(i * angleStep);
  }

  const gridLevels = [0.25, 0.5, 0.75, 1];
  const gridPolygons = gridLevels.map((pct) =>
    Array.from({ length: N }, (_, i) => `${polarX(i, radius * pct)},${polarY(i, radius * pct)}`).join(' ')
  );

  const valueToRadius = (val: number) => {
    const safeVal = Math.max(0, Number(val) || 0);
    const ratio = Math.min(safeVal / 10, 1);
    return ratio * radius;
  };

  const dataPolygon = scoreEntries
    .map(([, val], i) => `${polarX(i, valueToRadius(Number(val)))},${polarY(i, valueToRadius(Number(val)))}`)
    .join(' ');

  const gaugeScore = getAiOverallScore(aiDetail);
  const gaugeCx = 60;
  const gaugeCy = 60;
  const gaugeR = 48;
  const gaugeStrokeW = 9;
  const gaugeColor = gaugeScore >= 7 ? '#3b82f6' : gaugeScore >= 4 ? '#f59e0b' : '#ef4444';
  const gaugeCircumference = 2 * Math.PI * gaugeR;
  const gaugeFill = Math.min(gaugeScore / 10, 1);

  const normPriority = (p: string): string => {
    if (p === '高') return 'High';
    if (p === '中') return 'Medium';
    if (p === '低') return 'Low';
    return p;
  };

  const filteredIssues = aiIssueFilter.length === 0
    ? aiDetail?.issues ?? []
    : (aiDetail?.issues ?? []).filter((iss: any) => aiIssueFilter.includes(normPriority(iss.priority)));

  const priorityStyle: Record<string, string> = {
    High: 'bg-red-500 text-white',
    Medium: 'bg-orange-500 text-white',
    Low: 'bg-blue-500 text-white',
  };

  const summaryText = String(aiDetail?.overall_evaluation?.summary || '').trim();

  // Responsive scaling
  const panelRef = useRef<HTMLDivElement>(null);
  const [panelWidth, setPanelWidth] = useState(620);
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => setPanelWidth(entries[0].contentRect.width));
    ro.observe(el);
    if (el.clientWidth) setPanelWidth(el.clientWidth);
    return () => ro.disconnect();
  }, []);
  const DESIGN_W = 620;
  const scale = Math.min(panelWidth / DESIGN_W, 1);
  const gaugeRendered = Math.round(120 * scale);
  const radarRendered = Math.round(240 * scale);
  const fs = Math.max(11, Math.round(13 * scale));
  const labelW = Math.round(170 * scale);

  return (
    <div className="flex gap-5 pt-2">
      <div style={{ width: 310, flexShrink: 0 }} className="flex flex-col">
        {aiDetail?._attachmentId ? (
          <AuthenticatedImage
            src={`${apiUrl}/ea-requests/attachments/${aiDetail._attachmentId}/download`}
            alt="Architecture Diagram"
            style={{ width: 310, height: 'auto' }}
            className="object-contain rounded border border-gray-200"
            onClick={(blob) => {
              if (blob) {
                setViewerSrc(blob);
                setViewerOpen(true);
              }
            }}
          />
        ) : (
          <div className="w-full h-48 bg-gray-100 rounded border border-gray-200 flex items-center justify-center text-xs text-text-secondary">
            No image
          </div>
        )}
        {aiDetail?._archType && (
          <div className="mt-3 text-sm">
            <span className="text-text-secondary">{t('App Arch Type')}：</span>
            <span className="font-semibold text-text-primary">{aiDetail._archType}</span>
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0" ref={panelRef}>
        <div className="flex items-center gap-2 mb-3">
          <span style={{ fontSize: 18 }}>★</span>
          <span className="font-semibold text-text-primary" style={{ fontSize: fs + 2 }}>{t('Overall Evaluation')}</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Top-left: Gauge */}
          <div className="flex justify-center items-start pt-1">
            <svg width={gaugeRendered} height={gaugeRendered} viewBox="0 0 120 120">
              <circle cx={gaugeCx} cy={gaugeCy} r={gaugeR} fill="none" stroke="#e5e7eb" strokeWidth={gaugeStrokeW} />
              <circle
                cx={gaugeCx}
                cy={gaugeCy}
                r={gaugeR}
                fill="none"
                stroke={gaugeColor}
                strokeWidth={gaugeStrokeW}
                strokeLinecap="round"
                strokeDasharray={`${gaugeFill * gaugeCircumference} ${gaugeCircumference}`}
                transform={`rotate(-90 ${gaugeCx} ${gaugeCy})`}
              />
              <text x={gaugeCx} y={gaugeCy} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 28, fontWeight: 700, fill: '#1f2937' }}>
                {gaugeScore || gaugeScore === 0 ? gaugeScore : '-'}
              </text>
            </svg>
          </div>

          {/* Top-right: Description */}
          <div className="overflow-hidden">
            <p style={{ fontSize: fs, color: '#374151', lineHeight: 1.7, margin: 0 }}>
              {summaryText || t('No summary available')}
            </p>
          </div>

          {/* Bottom-left: Score bars */}
          <div className="overflow-hidden" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {scoreEntries.map(([key, val]) => {
              const n = Number(val) || 0;
              const pct = Math.min((n / 10) * 100, 100);
              return (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="text-text-secondary text-right shrink-0" style={{ width: labelW, fontSize: fs }}>
                    {formatAiScoreDimensionLabel(key)}
                  </span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden" style={{ minWidth: 20 }}>
                    <div className="h-full rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="font-semibold text-text-primary text-right shrink-0" style={{ width: Math.round(38 * scale), fontSize: fs }}>
                    {n.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Bottom-right: Radar */}
          <div className="overflow-hidden flex justify-center">
            {N >= 3 && (
              <svg width={radarRendered} height={radarRendered} viewBox={`0 0 ${radarSize} ${radarSize}`} style={{ overflow: 'visible', flexShrink: 0 }}>
                {gridPolygons.map((pts, idx) => (
                  <polygon key={idx} points={pts} fill="none" stroke="#e5e7eb" strokeWidth="1" />
                ))}
                {scoreEntries.map((_, i) => (
                  <line key={i} x1={cx} y1={cy} x2={polarX(i, radius)} y2={polarY(i, radius)} stroke="#e5e7eb" strokeWidth="1" />
                ))}
                <polygon points={dataPolygon} fill="rgba(59,130,246,0.2)" stroke="#3b82f6" strokeWidth="2" />
                {scoreEntries.map(([, val], i) => {
                  const r = valueToRadius(Number(val));
                  return <circle key={i} cx={polarX(i, r)} cy={polarY(i, r)} r="3" fill="#3b82f6" />;
                })}
                {scoreEntries.map(([key], i) => {
                  const labelR = radius + 18;
                  const x = polarX(i, labelR);
                  const y = polarY(i, labelR);
                  const anchor = Math.abs(x - cx) < 5 ? 'middle' : x > cx ? 'start' : 'end';
                  const label = formatAiScoreDimensionLabel(key);
                  return (
                    <text key={i} x={x} y={y} textAnchor={anchor} dominantBaseline="central" style={{ fontSize: 13, fill: '#6b7280' }}>
                      {label}
                    </text>
                  );
                })}
              </svg>
            )}
          </div>
        </div>

        {Array.isArray(aiDetail?.issues) && aiDetail.issues.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <InfoCircleOutlined style={{ color: '#f97316', fontSize: 16 }} />
                <h4 className="text-sm font-semibold text-text-primary">{t('Review Issues')}</h4>
              </div>
              <Select
                mode="multiple"
                size="small"
                value={aiIssueFilter}
                onChange={(vals: string[]) => setAiIssueFilter(vals)}
                placeholder={t('All Priorities')}
                maxTagCount={1}
                style={{ minWidth: 130 }}
                options={[
                  { value: 'High', label: t('High') },
                  { value: 'Medium', label: t('Medium') },
                  { value: 'Low', label: t('Low') },
                ]}
              />
            </div>
            <div className="space-y-3">
              {filteredIssues.map((issue: any) => (
                <div key={issue.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono font-bold text-sm text-text-primary">{issue.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${priorityStyle[normPriority(issue.priority)] ?? 'bg-gray-400 text-white'}`}>
                      {t(normPriority(issue.priority) ?? issue.priority)}
                    </span>
                    {issue.dimension && (
                      <span className="text-xs px-2 py-0.5 rounded border border-blue-300 text-blue-600">{issue.dimension}</span>
                    )}
                  </div>
                  {issue.related_entities && (
                    <p className="text-sm text-text-secondary mb-1">
                      <span className="font-medium">{t('Related Entities')}: </span>
                      {Array.isArray(issue.related_entities) ? issue.related_entities.join(', ') : issue.related_entities}
                    </p>
                  )}
                  {issue.description && (
                    <p className="text-sm text-text-secondary mb-2">
                      <span className="font-medium">{t('Impact')}: </span>
                      {issue.description}
                    </p>
                  )}
                  {issue.suggestion && (
                    <div className="bg-blue-50 rounded-md p-3">
                      <p className="text-sm font-medium text-text-primary mb-1">{t('Advice')}:</p>
                      <p className="text-sm text-text-secondary">{issue.suggestion}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
