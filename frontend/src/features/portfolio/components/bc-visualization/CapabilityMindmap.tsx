'use client';

import { useState, useMemo, useCallback, useRef } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, GitFork, Sun } from 'lucide-react';
import type { CapNode } from './types';
import { nodeMetrics, type Position, type NodeMetrics } from './geometry';
import { VIEWBOX_WIDTH, VIEWBOX_HEIGHT, TREE_CENTER_X } from './constants';
import { autoRadialPositions, autoTreePositions, treeHubY } from './layout-algorithms';
import { EdgeRenderer } from './EdgeRenderer';
import { NodeRenderer } from './NodeRenderer';
import { DomainFilter } from './DomainFilter';
import { DetailPanel } from './DetailPanel';

const SCALE_MIN = 0.35;
const SCALE_MAX = 2.0;
const SCALE_STEP = 0.15;

function loadPositions(): Record<string, Position> {
  try {
    const raw = localStorage.getItem('eam.bcv-node-positions');
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function savePositions(p: Record<string, Position>) {
  try {
    localStorage.setItem('eam.bcv-node-positions', JSON.stringify(p));
  } catch { /* quota exceeded */ }
}

interface CapabilityMindmapProps {
  capabilities: ReadonlyArray<CapNode>;
  domains: ReadonlyArray<string>;
}

export function CapabilityMindmap({ capabilities, domains }: CapabilityMindmapProps) {
  const [layoutMode, setLayoutMode] = useState<'star' | 'tree'>('star');
  const [scale, setScale] = useState(0.75);
  const [pan, setPan] = useState<Position>({ x: 0, y: 0 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [mutedDomains, setMutedDomains] = useState<Set<string>>(new Set());
  const [highlightMultiApps, setHighlightMultiApps] = useState(false);
  const [customPositions, setCustomPositions] = useState<Record<string, Position>>(loadPositions);

  const [dragging, setDragging] = useState<{ id: string; startX: number; startY: number; origX: number; origY: number } | null>(null);
  const [canvasDragging, setCanvasDragging] = useState<{ startX: number; startY: number; origPanX: number; origPanY: number } | null>(null);

  const svgRef = useRef<SVGSVGElement>(null);
  const [centerPos] = useState<Position>({ x: VIEWBOX_WIDTH / 2, y: VIEWBOX_HEIGHT / 2 });

  // Visible capabilities (respecting collapse)
  const visibleCaps = useMemo(() => {
    const hidden = new Set<string>();
    for (const cId of Array.from(collapsed)) {
      const addDescendants = (parentId: string) => {
        for (const c of capabilities) {
          if (c.parentId === parentId) {
            hidden.add(c.id);
            addDescendants(c.id);
          }
        }
      };
      addDescendants(cId);
    }
    return capabilities.filter((c) => !hidden.has(c.id));
  }, [capabilities, collapsed]);

  // Node metrics
  const metricsById = useMemo(() => {
    const result: Record<string, NodeMetrics> = {};
    for (const cap of visibleCaps) {
      result[cap.id] = nodeMetrics(cap.level, cap.name, cap.applications);
    }
    return result;
  }, [visibleCaps]);

  // Positions
  const positions = useMemo(() => {
    const auto =
      layoutMode === 'star'
        ? autoRadialPositions(visibleCaps, metricsById, centerPos.x, centerPos.y)
        : autoTreePositions(visibleCaps, metricsById);
    return { ...auto, ...customPositions };
  }, [visibleCaps, metricsById, layoutMode, centerPos, customPositions]);

  // Hub center for tree mode
  const hubCenter = useMemo((): Position => {
    if (layoutMode === 'tree') {
      const hubY = treeHubY(positions, visibleCaps, metricsById);
      return { x: TREE_CENTER_X, y: hubY };
    }
    return centerPos;
  }, [layoutMode, positions, visibleCaps, metricsById, centerPos]);

  // Muted nodes
  const mutedNodes = useMemo(() => {
    if (mutedDomains.size === 0) return new Set<string>();
    const muted = new Set<string>();
    for (const cap of visibleCaps) {
      if (mutedDomains.has(cap.domain)) muted.add(cap.id);
    }
    return muted;
  }, [visibleCaps, mutedDomains]);

  // Has children lookup
  const hasChildrenMap = useMemo(() => {
    const result = new Set<string>();
    for (const cap of capabilities) {
      if (cap.parentId) result.add(cap.parentId);
    }
    return result;
  }, [capabilities]);

  // Multi-app highlight set
  const multiAppIds = useMemo(() => {
    if (!highlightMultiApps) return new Set<string>();
    const appCapCount = new Map<string, number>();
    for (const cap of visibleCaps) {
      for (const app of cap.applications) {
        appCapCount.set(app.id, (appCapCount.get(app.id) ?? 0) + 1);
      }
    }
    const multiApps = new Set<string>();
    for (const [appId, count] of Array.from(appCapCount)) {
      if (count > 1) multiApps.add(appId);
    }
    const result = new Set<string>();
    for (const cap of visibleCaps) {
      if (cap.applications.some((a) => multiApps.has(a.id))) result.add(cap.id);
    }
    return result;
  }, [visibleCaps, highlightMultiApps]);

  const selectedCap = useMemo(
    () => capabilities.find((c) => c.id === selectedId) ?? null,
    [capabilities, selectedId],
  );

  // Interaction handlers
  const handleToggleDomain = useCallback((domain: string) => {
    setMutedDomains((prev) => {
      const next = new Set(prev);
      if (next.has(domain)) next.delete(domain); else next.add(domain);
      return next;
    });
  }, []);

  const handleFocusDomain = useCallback(
    (domain: string) => {
      setMutedDomains((prev) => {
        const allMutedExceptThis = new Set(domains.filter((d) => d !== domain));
        if (prev.size === allMutedExceptThis.size && Array.from(prev).every((d) => allMutedExceptThis.has(d))) {
          return new Set();
        }
        return allMutedExceptThis;
      });
    },
    [domains],
  );

  const handleToggleCollapse = useCallback((id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const toSvgPoint = useCallback(
    (clientX: number, clientY: number): Position => {
      const svg = svgRef.current;
      if (!svg) return { x: 0, y: 0 };
      const rect = svg.getBoundingClientRect();
      const scaleX = VIEWBOX_WIDTH / rect.width;
      const scaleY = VIEWBOX_HEIGHT / rect.height;
      return { x: (clientX - rect.left) * scaleX, y: (clientY - rect.top) * scaleY };
    },
    [],
  );

  const handleCanvasMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if ((e.target as SVGElement).closest('[data-role="node-root"]')) return;
      const pt = toSvgPoint(e.clientX, e.clientY);
      setCanvasDragging({ startX: pt.x, startY: pt.y, origPanX: pan.x, origPanY: pan.y });
    },
    [pan, toSvgPoint],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (dragging) {
        const pt = toSvgPoint(e.clientX, e.clientY);
        const dx = (pt.x - dragging.startX) / scale;
        const dy = (pt.y - dragging.startY) / scale;
        setCustomPositions((prev) => ({
          ...prev,
          [dragging.id]: { x: dragging.origX + dx, y: dragging.origY + dy },
        }));
        return;
      }
      if (canvasDragging) {
        const pt = toSvgPoint(e.clientX, e.clientY);
        const dx = pt.x - canvasDragging.startX;
        const dy = pt.y - canvasDragging.startY;
        setPan({ x: canvasDragging.origPanX + dx, y: canvasDragging.origPanY + dy });
      }
    },
    [dragging, canvasDragging, scale, toSvgPoint],
  );

  const handleMouseUp = useCallback(() => {
    if (dragging) savePositions(customPositions);
    setDragging(null);
    setCanvasDragging(null);
  }, [dragging, customPositions]);

  const handleNodeDragStartFixed = useCallback(
    (id: string) => {
      const p = positions[id];
      if (!p) return;
      setDragging(null);
      const startCapture = (e: MouseEvent) => {
        const pt = toSvgPoint(e.clientX, e.clientY);
        setDragging({ id, startX: pt.x, startY: pt.y, origX: p.x, origY: p.y });
        window.removeEventListener('mousemove', startCapture);
      };
      window.addEventListener('mousemove', startCapture, { once: true });
    },
    [positions, toSvgPoint],
  );

  const resetView = useCallback(() => {
    setScale(0.75);
    setPan({ x: 0, y: 0 });
    setCustomPositions({});
    savePositions({});
  }, []);

  const cx = VIEWBOX_WIDTH / 2;
  const cy = VIEWBOX_HEIGHT / 2;
  const tx = pan.x + cx * (1 - scale);
  const ty = pan.y + cy * (1 - scale);

  return (
    <div className="flex flex-col gap-3">
      {/* Controls bar */}
      <div className="bg-white rounded-lg border border-gray-200 flex flex-wrap items-center gap-3 px-4 py-3">
        <div className="flex items-center gap-1.5">
          <button
            className={`h-8 px-3 text-xs font-medium rounded flex items-center gap-1.5 transition-colors ${
              layoutMode === 'star'
                ? 'bg-primary-blue text-white'
                : 'border border-gray-300 text-text-primary hover:bg-gray-50'
            }`}
            onClick={() => setLayoutMode('star')}
          >
            <Sun className="h-3.5 w-3.5" />
            Radial
          </button>
          <button
            className={`h-8 px-3 text-xs font-medium rounded flex items-center gap-1.5 transition-colors ${
              layoutMode === 'tree'
                ? 'bg-primary-blue text-white'
                : 'border border-gray-300 text-text-primary hover:bg-gray-50'
            }`}
            onClick={() => setLayoutMode('tree')}
          >
            <GitFork className="h-3.5 w-3.5" />
            Tree
          </button>
        </div>

        <div className="h-5 w-px bg-gray-200" />

        <DomainFilter
          domains={domains}
          mutedDomains={mutedDomains}
          highlightMultiApps={highlightMultiApps}
          onToggleDomain={handleToggleDomain}
          onFocusDomain={handleFocusDomain}
          onToggleHighlight={() => setHighlightMultiApps((v) => !v)}
        />

        <div className="ml-auto flex items-center gap-1.5">
          <button
            className="h-8 w-8 flex items-center justify-center border border-gray-300 rounded hover:bg-gray-50"
            onClick={() => setScale((s) => Math.max(SCALE_MIN, s - SCALE_STEP))}
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="w-12 text-center text-xs text-gray-500">
            {Math.round(scale * 100)}%
          </span>
          <button
            className="h-8 w-8 flex items-center justify-center border border-gray-300 rounded hover:bg-gray-50"
            onClick={() => setScale((s) => Math.min(SCALE_MAX, s + SCALE_STEP))}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <button
            className="h-8 w-8 flex items-center justify-center border border-gray-300 rounded hover:bg-gray-50"
            onClick={resetView}
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="bg-white rounded-lg border border-gray-200 relative overflow-hidden" style={{ height: 'calc(100vh - 280px)' }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          className="h-full w-full"
          style={{ cursor: canvasDragging ? 'grabbing' : 'default' }}
          onMouseDown={handleCanvasMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <g transform={`translate(${tx}, ${ty}) scale(${scale})`}>
            {/* Center hub */}
            <circle cx={hubCenter.x} cy={hubCenter.y} r={18} fill="#f8fafc" stroke="#94a3b8" strokeWidth={2} />
            <text
              x={hubCenter.x} y={hubCenter.y + 1}
              textAnchor="middle" dominantBaseline="middle"
              fontSize={10} fill="#64748b" fontWeight={600}
            >
              HUB
            </text>

            <EdgeRenderer
              capabilities={visibleCaps}
              positions={positions}
              metricsById={metricsById}
              layoutMode={layoutMode}
              collapsed={collapsed}
              mutedNodes={mutedNodes}
              centerX={hubCenter.x}
              centerY={hubCenter.y}
            />

            {visibleCaps.map((cap) => {
              const pos = positions[cap.id];
              const m = metricsById[cap.id];
              if (!pos || !m) return null;

              return (
                <NodeRenderer
                  key={cap.id}
                  cap={cap}
                  pos={pos}
                  metrics={m}
                  isSelected={selectedId === cap.id}
                  isMuted={mutedNodes.has(cap.id)}
                  isHighlightedMultiApp={multiAppIds.has(cap.id)}
                  isCollapsed={collapsed.has(cap.id)}
                  hasChildren={hasChildrenMap.has(cap.id)}
                  onSelect={setSelectedId}
                  onToggleCollapse={handleToggleCollapse}
                  onDragStart={handleNodeDragStartFixed}
                />
              );
            })}
          </g>
        </svg>

        <DetailPanel cap={selectedCap} onClose={() => setSelectedId(null)} />
      </div>
    </div>
  );
}
