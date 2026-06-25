'use client';

import type { CapNode } from './types';
import { getDomainPalette } from './constants';

interface DetailPanelProps {
  readonly cap: CapNode | null;
  readonly onClose: () => void;
}

export function DetailPanel({ cap, onClose }: DetailPanelProps) {
  if (!cap) return null;

  const palette = getDomainPalette(cap.domain);

  return (
    <div className="absolute right-4 top-4 z-20 w-72 bg-white rounded-lg border border-gray-200 shadow-lg p-4">
      <div className="mb-3 flex items-start justify-between">
        <h3 className="text-sm font-semibold text-gray-900">{cap.name}</h3>
        <button
          onClick={onClose}
          className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          &times;
        </button>
      </div>

      {cap.nameCn && (
        <p className="mb-2 text-xs text-gray-500">{cap.nameCn}</p>
      )}

      <div className="mb-3 flex items-center gap-2">
        <span className="inline-block rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700">
          L{cap.level}
        </span>
        <span
          className="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
          style={{
            backgroundColor: palette.fill,
            color: palette.text,
            border: `1px solid ${palette.stroke}`,
          }}
        >
          {cap.domain}
        </span>
      </div>

      {cap.description && (
        <p className="mb-3 text-xs leading-relaxed text-gray-600">
          {cap.description}
        </p>
      )}

      <div className="border-t border-gray-100 pt-3">
        <p className="mb-2 text-xs font-medium text-gray-700">
          Applications ({cap.applications.length})
        </p>
        {cap.applications.length === 0 ? (
          <p className="text-xs text-gray-400">No applications mapped</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {cap.applications.map((app) => (
              <span
                key={app.id}
                className="inline-block rounded-md px-2 py-1 text-xs"
                style={{
                  backgroundColor: palette.fill,
                  color: palette.stroke,
                  border: `1px solid ${palette.stroke}40`,
                }}
              >
                {app.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
