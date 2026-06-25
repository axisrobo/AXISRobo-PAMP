'use client';

import { useState } from 'react';

export function RequestDetailSection({
  title,
  defaultOpen = true,
  badge: _badge,
  children,
  actions,
}: {
  title: string;
  defaultOpen?: boolean;
  badge?: number;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-border-default rounded-lg bg-white" style={{ marginBottom: '15px' }}>
      <div className="w-full flex items-center justify-between px-4 py-3 text-left">
        <div className="flex items-center gap-2">
          <div
            className="flex items-center gap-2 cursor-pointer"
            role="button"
            tabIndex={0}
            onClick={() => setOpen(!open)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                setOpen(!open);
              }
            }}
          >
            <span className="text-sm font-semibold text-text-primary">{title}</span>
          </div>
          {actions && (
            <div className="ml-2 flex-shrink-0" onClick={(event) => event.stopPropagation()}>
              {actions}
            </div>
          )}
        </div>
        <div>
          <button onClick={() => setOpen(!open)} aria-label={`Toggle ${title}`} className="text-text-secondary">
            <svg className={`w-4 h-4 transition-transform ${open ? '' : '-rotate-90'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}