'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Select, Spin, Tag } from 'antd';
import { api } from '@/shared/lib/api';

/**
 * Extract only the display name from a stored resource value string.
 * Handles formats:
 *   "email&&Full Name"   (current format, e.g. 'jsmith@example.com&&John Smith')
 *   "itcode&&Full Name"  (legacy format)
 *   "itcode-Full Name"   (old API format)
 */
function extractNameFromValue(value: string): string {
  // Current & legacy format: xxx&&Name
  if (value.includes('&&')) {
    return value.split('&&').slice(1).join('&&').trim();
  }
  // Old format: itcode-Name (lowercase letters + digits at start followed by '-')
  const match = value.match(/^[a-z][a-z0-9]*-(.+)$/i);
  if (match) return match[1].trim();
  return value;
}

interface ResourceOption {
  key: string;
  value: string;
  itcode: string;
  name: string;
  email?: string;
}

interface ResourceMultiSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  className?: string;
  limit?: number;
}

export function ResourceMultiSelect({
  value,
  onChange,
  placeholder = 'Search and select resources',
  className,
  limit = 100,
}: ResourceMultiSelectProps) {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data = [], isFetching } = useQuery<ResourceOption[]>({
    queryKey: ['resourceMultiSelect', debouncedSearch, limit],
    queryFn: () => api.get<ResourceOption[]>('/resources/search', { q: debouncedSearch, limit }),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const options = useMemo(() => {
    const remoteOptions = data.map((item) => ({
      key: item.key,
      value: item.value,
      label: `${item.itcode}-${item.name}`,
      title: item.key,
    }));

    const fallbackSelected = value
      .filter((selected) => !remoteOptions.some((option) => option.value === selected))
      .map((selected) => ({
        key: selected,
        value: selected,
        label: selected,
        title: selected,
      }));

    return [...fallbackSelected, ...remoteOptions];
  }, [data, value]);

  return (
    <Select
      mode="multiple"
      showSearch
      value={value}
      onChange={onChange}
      onSearch={setSearch}
      placeholder={placeholder}
      className={className}
      style={{ width: '100%' }}
      filterOption={false}
      options={options}
      maxTagCount={undefined}
      optionLabelProp="label"
      tagRender={({ label: _label, value: tagValue, closable, onClose }) => (
        <Tag closable={closable} onClose={onClose} style={{ marginInlineEnd: 4 }}>
          {extractNameFromValue(String(tagValue))}
        </Tag>
      )}
      notFoundContent={isFetching ? <Spin size="small" /> : debouncedSearch ? 'No matching resources' : 'Type to search'}
    />
  );
}