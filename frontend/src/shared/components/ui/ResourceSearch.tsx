'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';

interface ResourceItem {
  itcode: string;
  name: string;
  email: string;
  label: string;
}

interface ResourceSearchProps {
  value: string;
  onChange: (value: string, resource?: ResourceItem) => void;
  placeholder?: string;
  className?: string;
  multiple?: boolean;
}

export function ResourceSearch({ value, onChange, placeholder = 'Search by name or IT code...', className = '' }: ResourceSearchProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: results = [] } = useQuery<ResourceItem[]>({
    queryKey: ['resourceSearch', query],
    queryFn: () => api.get<ResourceItem[]>('/resources/search', { q: query }),
    enabled: query.length >= 2,
    staleTime: 30_000,
  });

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSelect = (item: ResourceItem) => {
    onChange(item.label, item);
    setQuery('');
    setOpen(false);
  };

  return (
    <div ref={ref} className={`relative ${className}`}>
      <input
        type="text"
        value={open ? query : value}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
          if (!e.target.value) onChange('');
        }}
        onFocus={() => {
          setQuery('');
          setOpen(true);
        }}
        placeholder={placeholder}
        className="w-full border border-border-default rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-blue"
      />
      {open && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-border-default rounded-lg shadow-lg max-h-60 overflow-auto">
          {results.map((item) => (
            <button
              key={item.itcode}
              type="button"
              onClick={() => handleSelect(item)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 flex items-center justify-between"
            >
              <span>
                <span className="font-medium text-text-primary">{item.name}</span>
                <span className="text-text-secondary ml-2">({item.itcode})</span>
              </span>
              <span className="text-xs text-text-secondary">{item.email}</span>
            </button>
          ))}
        </div>
      )}
      {open && query.length >= 2 && results.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-border-default rounded-lg shadow-lg p-3 text-sm text-text-secondary text-center">
          No results found
        </div>
      )}
    </div>
  );
}
