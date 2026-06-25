'use client';

import { useMemo } from 'react';
import type { CapNode } from './types';
import type { Position, NodeMetrics } from './geometry';
import { rectAnchorToward, curvePath } from './geometry';

interface EdgeRendererProps {
  readonly capabilities: ReadonlyArray<CapNode>;
  readonly positions: Record<string, Position>;
  readonly metricsById: Record<string, NodeMetrics>;
  readonly layoutMode: 'star' | 'tree';
  readonly collapsed: Set<string>;
  readonly mutedNodes: Set<string>;
  readonly centerX: number;
  readonly centerY: number;
}

export function EdgeRenderer({
  capabilities, positions, metricsById, layoutMode,
  collapsed, mutedNodes, centerX, centerY,
}: EdgeRendererProps) {
  const edges = useMemo(() => {
    const result: { key: string; d: string; muted: boolean }[] = [];

    const hubPoint: Position = { x: centerX, y: centerY };

    for (const cap of capabilities) {
      if (!cap.parentId) {
        const pos = positions[cap.id];
        const m = metricsById[cap.id];
        if (!pos || !m) continue;

        const anchor = rectAnchorToward(pos.x, pos.y, m.width, m.height, hubPoint.x, hubPoint.y);
        const d = curvePath(hubPoint, anchor, layoutMode);
        result.push({ key: `hub-${cap.id}`, d, muted: mutedNodes.has(cap.id) });
        continue;
      }

      if (collapsed.has(cap.parentId)) continue;

      const parentPos = positions[cap.parentId];
      const parentMetrics = metricsById[cap.parentId];
      const childPos = positions[cap.id];
      const childMetrics = metricsById[cap.id];

      if (!parentPos || !parentMetrics || !childPos || !childMetrics) continue;

      const pCenter: Position = {
        x: parentPos.x + parentMetrics.width / 2,
        y: parentPos.y + parentMetrics.height / 2,
      };
      const cCenter: Position = {
        x: childPos.x + childMetrics.width / 2,
        y: childPos.y + childMetrics.height / 2,
      };

      const p1 = rectAnchorToward(
        parentPos.x, parentPos.y, parentMetrics.width, parentMetrics.height,
        cCenter.x, cCenter.y,
      );
      const p2 = rectAnchorToward(
        childPos.x, childPos.y, childMetrics.width, childMetrics.height,
        pCenter.x, pCenter.y,
      );

      const d = curvePath(p1, p2, layoutMode);
      const muted = mutedNodes.has(cap.id) || mutedNodes.has(cap.parentId);
      result.push({ key: `${cap.parentId}-${cap.id}`, d, muted });
    }

    return result;
  }, [capabilities, positions, metricsById, layoutMode, collapsed, mutedNodes, centerX, centerY]);

  return (
    <g data-role="edges">
      {edges.map((edge) => (
        <path
          key={edge.key}
          d={edge.d}
          fill="none"
          stroke={edge.muted ? '#e2e8f0' : '#94a3b8'}
          strokeWidth={edge.muted ? 1 : 1.5}
          opacity={edge.muted ? 0.4 : 0.7}
        />
      ))}
    </g>
  );
}
