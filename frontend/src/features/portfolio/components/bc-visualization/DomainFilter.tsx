'use client';

import { useCallback, useRef } from 'react';
import { getDomainPalette } from './constants';

interface DomainFilterProps {
  readonly domains: ReadonlyArray<string>;
  readonly mutedDomains: Set<string>;
  readonly highlightMultiApps: boolean;
  readonly onToggleDomain: (domain: string) => void;
  readonly onFocusDomain: (domain: string) => void;
  readonly onToggleHighlight: () => void;
}

export function DomainFilter({
  domains, mutedDomains, highlightMultiApps,
  onToggleDomain, onFocusDomain, onToggleHighlight,
}: DomainFilterProps) {
  const clickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clickDomainRef = useRef<string | null>(null);

  const handleClick = useCallback(
    (domain: string) => {
      if (clickTimerRef.current && clickDomainRef.current === domain) {
        clearTimeout(clickTimerRef.current);
        clickTimerRef.current = null;
        clickDomainRef.current = null;
        onFocusDomain(domain);
        return;
      }

      clickDomainRef.current = domain;
      clickTimerRef.current = setTimeout(() => {
        clickTimerRef.current = null;
        clickDomainRef.current = null;
        onToggleDomain(domain);
      }, 220);
    },
    [onToggleDomain, onFocusDomain],
  );

  return (
    <div className="flex flex-wrap items-center gap-2">
      {domains.map((domain) => {
        const palette = getDomainPalette(domain);
        const muted = mutedDomains.has(domain);
        return (
          <button
            key={domain}
            onClick={() => handleClick(domain)}
            className="rounded-full px-3 py-1 text-xs font-medium transition"
            style={{
              backgroundColor: muted ? '#f1f5f9' : palette.fill,
              color: muted ? '#94a3b8' : palette.text,
              border: `1.5px solid ${muted ? '#cbd5e1' : palette.stroke}`,
              opacity: muted ? 0.6 : 1,
            }}
          >
            {domain}
          </button>
        );
      })}
      <label className="ml-4 flex items-center gap-1.5 text-xs text-gray-500">
        <input
          type="checkbox"
          checked={highlightMultiApps}
          onChange={onToggleHighlight}
          className="rounded"
        />
        Highlight multi-app capabilities
      </label>
    </div>
  );
}
