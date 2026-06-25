export const VIEWBOX_WIDTH = 1900;
export const VIEWBOX_HEIGHT = 1200;
export const MIN_NODE_WIDTH = 280;
export const MAX_NODE_WIDTH = 980;
export const APP_BOX_HEIGHT = 36;
export const APP_BOX_GAP = 12;
export const NODE_INNER_GAP = 14;
export const TITLE_FONT_SIZE = 16;
export const APP_FONT_SIZE = 14;
export const TREE_COLUMN_GAP = 360;
export const TREE_CENTER_X = 320;

export interface DomainPalette {
  readonly fill: string;
  readonly stroke: string;
  readonly text: string;
  readonly mutedFill: string;
  readonly mutedStroke: string;
  readonly mutedText: string;
}

const MUTED = {
  mutedFill: '#f1f5f9',
  mutedStroke: '#cbd5e1',
  mutedText: '#94a3b8',
};

export const DOMAIN_PALETTE: Record<string, DomainPalette> = {
  Sales: { fill: '#bfdbfe', stroke: '#1e3a8a', text: '#0a0a0a', ...MUTED },
  Service: { fill: '#a5f3fc', stroke: '#155e75', text: '#0a0a0a', ...MUTED },
  Finance: { fill: '#ddd6fe', stroke: '#4c1d95', text: '#0a0a0a', ...MUTED },
  'Intelligent Operation': { fill: '#fde68a', stroke: '#92400e', text: '#0a0a0a', ...MUTED },
  DTIT: { fill: '#bbf7d0', stroke: '#166534', text: '#0a0a0a', ...MUTED },
  'Product Development': { fill: '#fecaca', stroke: '#991b1b', text: '#0a0a0a', ...MUTED },
  Marketing: { fill: '#fed7aa', stroke: '#9a3412', text: '#0a0a0a', ...MUTED },
  'Supply Chain': { fill: '#fbcfe8', stroke: '#9d174d', text: '#0a0a0a', ...MUTED },
  Other: { fill: '#cbd5e1', stroke: '#1f2937', text: '#0a0a0a', ...MUTED },
};

export function getDomainPalette(domain: string): DomainPalette {
  return DOMAIN_PALETTE[domain] ?? DOMAIN_PALETTE['Other'];
}
