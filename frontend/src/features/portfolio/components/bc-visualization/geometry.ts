import type { AppRef } from './types';
import {
  APP_BOX_HEIGHT,
  APP_BOX_GAP,
  APP_FONT_SIZE,
  NODE_INNER_GAP,
  TITLE_FONT_SIZE,
  MIN_NODE_WIDTH,
  MAX_NODE_WIDTH,
} from './constants';

export interface Position {
  readonly x: number;
  readonly y: number;
}

export interface NodeMetrics {
  readonly width: number;
  readonly height: number;
  readonly headerHeight: number;
}

function estimateTextWidth(text: string, fontSize = 14): number {
  const cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const other = text.length - cjk;
  const units = cjk * 1.05 + other * 0.62;
  return units * fontSize;
}

export function polarToXY(cx: number, cy: number, r: number, angleRad: number): Position {
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

export function appBoxWidth(name: string): number {
  return estimateTextWidth(name, APP_FONT_SIZE) + 20;
}

export function splitRows(apps: ReadonlyArray<AppRef>, cols: number): AppRef[][] {
  const rows: AppRef[][] = [];
  for (let i = 0; i < apps.length; i += cols) {
    rows.push(apps.slice(i, i + cols) as AppRef[]);
  }
  return rows;
}

export function nodeMetrics(
  level: number,
  name: string,
  apps: ReadonlyArray<AppRef>,
): NodeMetrics {
  const title = `L${level} \u00b7 ${name}`;
  const titleWidth = estimateTextWidth(title, TITLE_FONT_SIZE) + NODE_INNER_GAP * 2;

  const widths = apps.map((a) => appBoxWidth(a.name));
  const longest = widths.length ? Math.max(...widths) : 140;
  const cols = longest <= 170 && apps.length >= 3 ? 3 : 2;

  const rows = splitRows(apps, cols);
  const rowWidths = rows.map((row) =>
    row.reduce((s, app, i) => s + appBoxWidth(app.name) + (i > 0 ? APP_BOX_GAP : 0), 0),
  );
  const appBandWidth = Math.max(180, ...rowWidths);

  const width = Math.max(
    MIN_NODE_WIDTH,
    Math.min(MAX_NODE_WIDTH, Math.max(titleWidth, appBandWidth + NODE_INNER_GAP * 2 + 12)),
  );
  const appRows = Math.max(1, rows.length);
  const headerHeight = 52;
  const appAreaHeight = appRows * APP_BOX_HEIGHT + (appRows - 1) * 10 + 16;
  const height = headerHeight + appAreaHeight;

  return { width, height, headerHeight };
}

export function rectAnchorToward(
  rx: number, ry: number, rw: number, rh: number,
  tx: number, ty: number,
): Position {
  const cx = rx + rw / 2;
  const cy = ry + rh / 2;
  const dx = tx - cx;
  const dy = ty - cy;
  if (dx === 0 && dy === 0) return { x: cx, y: cy };

  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);
  const hw = rw / 2;
  const hh = rh / 2;

  let scale: number;
  if (absDx * hh > absDy * hw) {
    scale = hw / absDx;
  } else {
    scale = hh / absDy;
  }

  return { x: cx + dx * scale, y: cy + dy * scale };
}

export function curvePath(
  p1: Position, p2: Position, layoutMode: 'star' | 'tree',
): string {
  if (layoutMode === 'tree') {
    const midX = (p1.x + p2.x) / 2;
    return `M ${p1.x} ${p1.y} C ${midX} ${p1.y}, ${midX} ${p2.y}, ${p2.x} ${p2.y}`;
  }

  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const cx1 = p1.x + dx * 0.35;
  const cy1 = p1.y + dy * 0.35;
  const cx2 = p1.x + dx * 0.65;
  const cy2 = p1.y + dy * 0.65;
  return `M ${p1.x} ${p1.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p2.x} ${p2.y}`;
}
