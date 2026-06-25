import type { CapNode } from './types';
import type { Position, NodeMetrics } from './geometry';
import { polarToXY } from './geometry';
import { TREE_COLUMN_GAP, TREE_CENTER_X } from './constants';

export function autoRadialPositions(
  capabilities: ReadonlyArray<CapNode>,
  metricsById: Record<string, NodeMetrics>,
  centerX: number,
  centerY: number,
): Record<string, Position> {
  const pos: Record<string, Position> = {};
  const r1 = 260;
  const r2 = 520;
  const r3 = 780;

  const l1Nodes = capabilities
    .filter((c) => c.level === 1)
    .sort((a, b) => a.name.localeCompare(b.name, 'en'));

  const sectorSpan = l1Nodes.length > 0 ? (Math.PI * 2) / l1Nodes.length : 0;

  l1Nodes.forEach((l1, i) => {
    const angle = sectorSpan * i - Math.PI / 2;
    const { x, y } = polarToXY(centerX, centerY, r1, angle);
    const m = metricsById[l1.id];
    pos[l1.id] = { x: x - (m?.width ?? 280) / 2, y: y - (m?.height ?? 80) / 2 };

    const l2Children = capabilities
      .filter((c) => c.level === 2 && c.parentId === l1.id)
      .sort((a, b) => a.name.localeCompare(b.name, 'en'));

    if (l2Children.length === 0) return;

    const l2Span = Math.min(sectorSpan * 0.78, Math.PI / 2.2);
    const l2Start = angle - l2Span / 2;
    const l2Step = l2Children.length > 1 ? l2Span / (l2Children.length - 1) : 0;

    l2Children.forEach((l2, j) => {
      const l2Angle = l2Children.length === 1 ? angle : l2Start + l2Step * j;
      const p2 = polarToXY(centerX, centerY, r2, l2Angle);
      const m2 = metricsById[l2.id];
      pos[l2.id] = { x: p2.x - (m2?.width ?? 280) / 2, y: p2.y - (m2?.height ?? 80) / 2 };

      const l3Children = capabilities
        .filter((c) => c.level === 3 && c.parentId === l2.id)
        .sort((a, b) => a.name.localeCompare(b.name, 'en'));

      if (l3Children.length === 0) return;

      const l3Span = Math.min(l2Step > 0 ? l2Step * 0.62 : sectorSpan * 0.3, Math.PI / 3);
      const l3Start = l2Angle - l3Span / 2;
      const l3Step = l3Children.length > 1 ? l3Span / (l3Children.length - 1) : 0;

      l3Children.forEach((l3, k) => {
        const l3Angle = l3Children.length === 1 ? l2Angle : l3Start + l3Step * k;
        const p3 = polarToXY(centerX, centerY, r3, l3Angle);
        const m3 = metricsById[l3.id];
        pos[l3.id] = { x: p3.x - (m3?.width ?? 280) / 2, y: p3.y - (m3?.height ?? 80) / 2 };
      });
    });
  });

  return pos;
}

export function autoTreePositions(
  capabilities: ReadonlyArray<CapNode>,
  metricsById: Record<string, NodeMetrics>,
): Record<string, Position> {
  const pos: Record<string, Position> = {};
  const verticalGap = 36;
  let cursorY = 120;

  function getChildren(parentId: string, level: number): CapNode[] {
    return capabilities
      .filter((c) => c.parentId === parentId && c.level === level)
      .sort((a, b) => a.name.localeCompare(b.name, 'en'));
  }

  function layoutNode(node: CapNode): { minY: number; maxY: number } {
    const m = metricsById[node.id] ?? { width: 280, height: 80 };
    const x =
      node.level === 1
        ? TREE_CENTER_X + TREE_COLUMN_GAP
        : node.level === 2
          ? TREE_CENTER_X + TREE_COLUMN_GAP * 2
          : TREE_CENTER_X + TREE_COLUMN_GAP * 3;

    const childLevel = node.level + 1;
    const children = childLevel <= 3 ? getChildren(node.id, childLevel as 1 | 2 | 3) : [];

    if (children.length === 0) {
      const y = cursorY;
      pos[node.id] = { x, y };
      cursorY += m.height + verticalGap;
      return { minY: y, maxY: y + m.height };
    }

    const childBounds = children.map((child) => layoutNode(child));
    const childMinY = Math.min(...childBounds.map((b) => b.minY));
    const childMaxY = Math.max(...childBounds.map((b) => b.maxY));
    const centerChildY = (childMinY + childMaxY) / 2;

    const y = centerChildY - m.height / 2;
    pos[node.id] = { x, y };

    return { minY: Math.min(y, childMinY), maxY: Math.max(y + m.height, childMaxY) };
  }

  const l1Nodes = capabilities
    .filter((c) => c.level === 1)
    .sort((a, b) => a.name.localeCompare(b.name, 'en'));

  for (const l1 of l1Nodes) {
    layoutNode(l1);
  }

  return pos;
}

export function treeHubY(
  layout: Record<string, Position>,
  capabilities: ReadonlyArray<CapNode>,
  metricsById: Record<string, NodeMetrics>,
): number {
  const l1Positions = capabilities
    .filter((c) => c.level === 1)
    .map((c) => {
      const p = layout[c.id];
      const m = metricsById[c.id];
      return p && m ? p.y + m.height / 2 : 0;
    })
    .filter((y) => y !== 0);

  if (l1Positions.length === 0) return 600;
  return (Math.min(...l1Positions) + Math.max(...l1Positions)) / 2;
}
