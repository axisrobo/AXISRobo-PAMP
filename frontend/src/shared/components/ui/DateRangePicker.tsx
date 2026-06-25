'use client';

import { useState } from 'react';
import { Calendar } from 'lucide-react';
import clsx from 'clsx';

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onStartChange: (date: string) => void;
  onEndChange: (date: string) => void;
  label?: string;
  className?: string;
  disabled?: boolean;
}

export function DateRangePicker({
  startDate,
  endDate,
  onStartChange,
  onEndChange,
  label,
  className = '',
  disabled = false,
}: DateRangePickerProps) {
  return (
    <div className={className}>
      {label && <label className="block text-xs text-text-secondary mb-1">{label}</label>}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartChange(e.target.value)}
            max={endDate || undefined}
            disabled={disabled}
            className={clsx(
              'input-field !pl-9',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          />
        </div>
        <span className="text-text-secondary text-sm">to</span>
        <div className="relative flex-1">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary pointer-events-none" />
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndChange(e.target.value)}
            min={startDate || undefined}
            disabled={disabled}
            className={clsx(
              'input-field !pl-9',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          />
        </div>
      </div>
    </div>
  );
}

// Preset quick-select ranges
export function DateRangePresets({
  onSelect,
  className = '',
}: {
  onSelect: (start: string, end: string) => void;
  className?: string;
}) {
  const today = new Date();
  const fmt = (d: Date) => d.toISOString().split('T')[0];

  const presets = [
    {
      label: 'Last 7 days',
      range: () => {
        const s = new Date(today);
        s.setDate(s.getDate() - 7);
        return [fmt(s), fmt(today)];
      },
    },
    {
      label: 'Last 30 days',
      range: () => {
        const s = new Date(today);
        s.setDate(s.getDate() - 30);
        return [fmt(s), fmt(today)];
      },
    },
    {
      label: 'Last 90 days',
      range: () => {
        const s = new Date(today);
        s.setDate(s.getDate() - 90);
        return [fmt(s), fmt(today)];
      },
    },
    {
      label: 'This year',
      range: () => {
        const s = new Date(today.getFullYear(), 0, 1);
        return [fmt(s), fmt(today)];
      },
    },
  ];

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      {presets.map((p) => (
        <button
          key={p.label}
          type="button"
          onClick={() => {
            const [s, e] = p.range();
            onSelect(s, e);
          }}
          className="text-xs px-2 py-1 rounded border border-border-light text-text-secondary hover:text-primary-blue hover:border-primary-blue transition-colors"
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}
