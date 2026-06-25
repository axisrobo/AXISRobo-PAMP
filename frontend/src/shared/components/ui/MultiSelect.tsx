'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { X, ChevronDown, Search } from 'lucide-react';
import clsx from 'clsx';

export interface MultiSelectOption {
  value: string;
  label: string;
  description?: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  className?: string;
  disabled?: boolean;
  maxDisplay?: number;
  loading?: boolean;
  onSearch?: (query: string) => void;
}

export function MultiSelect({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  searchPlaceholder = 'Type to search...',
  className = '',
  disabled = false,
  maxDisplay = 5,
  loading = false,
  onSearch,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Debounced external search
  useEffect(() => {
    if (!onSearch) return;
    const timer = setTimeout(() => onSearch(query), 300);
    return () => clearTimeout(timer);
  }, [query, onSearch]);

  const filtered = query
    ? options.filter(
        (opt) =>
          opt.label.toLowerCase().includes(query.toLowerCase()) ||
          opt.value.toLowerCase().includes(query.toLowerCase()) ||
          (opt.description?.toLowerCase().includes(query.toLowerCase()) ?? false)
      )
    : options;

  const toggle = useCallback(
    (val: string) => {
      if (value.includes(val)) {
        onChange(value.filter((v) => v !== val));
      } else {
        onChange([...value, val]);
      }
    },
    [value, onChange]
  );

  const remove = useCallback(
    (val: string) => {
      onChange(value.filter((v) => v !== val));
    },
    [value, onChange]
  );

  const selectedLabels = value
    .map((v) => options.find((o) => o.value === v))
    .filter(Boolean) as MultiSelectOption[];

  return (
    <div ref={containerRef} className={clsx('relative', className)}>
      {/* Trigger */}
      <div
        onClick={() => {
          if (!disabled) {
            setOpen(!open);
            setTimeout(() => inputRef.current?.focus(), 0);
          }
        }}
        className={clsx(
          'flex flex-wrap items-center gap-1 min-h-[38px] px-3 py-1.5 border rounded cursor-pointer transition-colors',
          open ? 'border-primary-blue ring-1 ring-primary-blue' : 'border-border-light hover:border-gray-400',
          disabled && 'opacity-50 cursor-not-allowed bg-gray-50'
        )}
      >
        {selectedLabels.length === 0 && (
          <span className="text-sm text-text-secondary">{placeholder}</span>
        )}
        {selectedLabels.slice(0, maxDisplay).map((item) => (
          <span
            key={item.value}
            className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-primary-blue text-xs rounded-full border border-blue-200"
          >
            {item.label}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); remove(item.value); }}
              className="p-0.5 rounded-full hover:bg-blue-100 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        {selectedLabels.length > maxDisplay && (
          <span className="text-xs text-text-secondary">+{selectedLabels.length - maxDisplay} more</span>
        )}
        <ChevronDown className={clsx('w-4 h-4 text-text-secondary ml-auto transition-transform', open && 'rotate-180')} />
      </div>

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-border-light rounded-lg shadow-lg overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-border-light">
            <Search className="w-4 h-4 text-text-secondary flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full text-sm outline-none bg-transparent"
            />
          </div>

          {/* Options */}
          <div className="max-h-60 overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <div className="w-5 h-5 border-2 border-primary-blue border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-4 text-center text-sm text-text-secondary">No options found</div>
            ) : (
              filtered.map((opt) => {
                const selected = value.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggle(opt.value)}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-sm hover:bg-blue-50 flex items-center gap-3 transition-colors',
                      selected && 'bg-blue-50/50'
                    )}
                  >
                    <div className={clsx(
                      'w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors',
                      selected ? 'bg-primary-blue border-primary-blue' : 'border-gray-300'
                    )}>
                      {selected && (
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="block text-text-primary">{opt.label}</span>
                      {opt.description && (
                        <span className="block text-xs text-text-secondary truncate">{opt.description}</span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Footer */}
          {value.length > 0 && (
            <div className="flex items-center justify-between px-3 py-2 border-t border-border-light bg-gray-50">
              <span className="text-xs text-text-secondary">{value.length} selected</span>
              <button
                type="button"
                onClick={() => onChange([])}
                className="text-xs text-primary-blue hover:underline"
              >
                Clear all
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
