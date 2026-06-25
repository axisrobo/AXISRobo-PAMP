'use client';

import type { CapNode } from './types';
import type { Position, NodeMetrics } from './geometry';
import { appBoxWidth, splitRows } from './geometry';
import {
  APP_BOX_HEIGHT,
  APP_BOX_GAP,
  APP_FONT_SIZE,
  NODE_INNER_GAP,
  TITLE_FONT_SIZE,
  getDomainPalette,
} from './constants';

interface NodeRendererProps {
  readonly cap: CapNode;
  readonly pos: Position;
  readonly metrics: NodeMetrics;
  readonly isSelected: boolean;
  readonly isMuted: boolean;
  readonly isHighlightedMultiApp: boolean;
  readonly isCollapsed: boolean;
  readonly hasChildren: boolean;
  readonly onSelect: (id: string) => void;
  readonly onToggleCollapse: (id: string) => void;
  readonly onDragStart: (id: string, svgX: number, svgY: number) => void;
}

export function NodeRenderer({
  cap, pos, metrics, isSelected, isMuted, isHighlightedMultiApp,
  isCollapsed, hasChildren, onSelect, onToggleCollapse, onDragStart,
}: NodeRendererProps) {
  const palette = getDomainPalette(cap.domain);
  const fill = isMuted ? palette.mutedFill : '#ffffff';
  const stroke = isHighlightedMultiApp
    ? '#dc2626'
    : isSelected
      ? '#000000'
      : isMuted
        ? palette.mutedStroke
        : '#cbd5e1';
  const textColor = isMuted ? palette.mutedText : '#0f172a';

  const cols = (() => {
    const widths = cap.applications.map((a) => appBoxWidth(a.name));
    const longest = widths.length ? Math.max(...widths) : 140;
    return longest <= 170 && cap.applications.length >= 3 ? 3 : 2;
  })();

  const rows = splitRows(cap.applications, cols);

  return (
    <g
      data-role="node-root"
      data-id={cap.id}
      style={{ cursor: 'grab' }}
      onMouseDown={(e) => {
        if ((e.target as SVGElement).closest('[data-role="collapse-group"]')) return;
        e.stopPropagation();
        onDragStart(cap.id, pos.x, pos.y);
      }}
      onClick={(e) => {
        if ((e.target as SVGElement).closest('[data-role="collapse-group"]')) return;
        e.stopPropagation();
        onSelect(cap.id);
      }}
    >
      <rect
        x={pos.x} y={pos.y} width={metrics.width} height={metrics.height}
        rx={14} fill={fill} stroke={stroke}
        strokeWidth={isSelected || isHighlightedMultiApp ? 2.5 : 1.5}
        filter={isSelected ? undefined : 'drop-shadow(0 1px 3px rgba(0,0,0,0.08))'}
      />

      {/* Domain color bar */}
      <rect
        x={pos.x} y={pos.y} width={metrics.width} height={6} rx={3}
        fill={isMuted ? palette.mutedStroke : palette.fill}
        clipPath="inset(0 0 0 0 round 14px 14px 0 0)"
      />

      {/* Title */}
      <text
        x={pos.x + NODE_INNER_GAP} y={pos.y + 30}
        fontSize={TITLE_FONT_SIZE} fontWeight={600} fill={textColor}
      >
        L{cap.level} &middot; {cap.name}
      </text>

      {/* Collapse button for L1/L2 with children */}
      {hasChildren && cap.level <= 2 && (
        <g
          data-role="collapse-group"
          style={{ cursor: 'pointer' }}
          onClick={(e) => { e.stopPropagation(); onToggleCollapse(cap.id); }}
        >
          <rect
            x={pos.x + metrics.width - 36} y={pos.y + 12}
            width={24} height={24} rx={6}
            fill="#f1f5f9" stroke="#cbd5e1" strokeWidth={1}
          />
          <text
            x={pos.x + metrics.width - 24} y={pos.y + 29}
            fontSize={14} fontWeight={700} fill="#475569" textAnchor="middle"
          >
            {isCollapsed ? '+' : '\u2212'}
          </text>
        </g>
      )}

      {/* Application badges */}
      {rows.map((row, rowIdx) => {
        let cursorX = pos.x + NODE_INNER_GAP;
        return row.map((app) => {
          const w = appBoxWidth(app.name);
          const bx = cursorX;
          const by = pos.y + metrics.headerHeight + rowIdx * (APP_BOX_HEIGHT + 10);
          cursorX += w + APP_BOX_GAP;

          const appPalette = getDomainPalette(cap.domain);

          return (
            <g key={app.id + '-' + cap.id + '-' + rowIdx}>
              <rect
                x={bx} y={by} width={w} height={APP_BOX_HEIGHT} rx={8}
                fill={isMuted ? appPalette.mutedFill : appPalette.fill}
                stroke={isMuted ? appPalette.mutedStroke : appPalette.stroke}
                strokeWidth={1}
              />
              <text
                x={bx + 10} y={by + APP_BOX_HEIGHT / 2 + 1}
                fontSize={APP_FONT_SIZE}
                fill={isMuted ? appPalette.mutedText : appPalette.text}
                dominantBaseline="middle"
              >
                {app.name}
              </text>
            </g>
          );
        });
      })}
    </g>
  );
}
