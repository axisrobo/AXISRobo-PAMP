'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AutoComplete, Typography } from 'antd';
import { api } from '@/shared/lib/api';

const { Text } = Typography;

interface ResourceItem {
  itcode: string;
  name: string;
  email: string;
  label: string;
}

interface ResourceAutoCompleteProps {
  value?: string;
  onChange?: (value: string, resource?: ResourceItem) => void;
  placeholder?: string;
  disabled?: boolean;
  style?: React.CSSProperties;
}

/**
 * Ant Design AutoComplete for searching resources by IT code or name.
 * Shows 100 records by default; filters with fuzzy match as you type.
 * Calls `/api/resources/search?q=xxx&limit=100`.
 */
export function ResourceAutoComplete({
  value = '',
  onChange,
  placeholder = 'Search by name or IT code',
  disabled = false,
  style,
}: ResourceAutoCompleteProps) {
  const [searchText, setSearchText] = useState('');

  const { data: results = [] } = useQuery<ResourceItem[]>({
    queryKey: ['resourceSearch', searchText],
    queryFn: () => api.get<ResourceItem[]>('/resources/search', { q: searchText, limit: 100 }),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const options = useMemo(() => results.map((item) => ({
    value: item.label,
    key: item.itcode,
    resource: item,
    label: item.label,
  })), [results]);

  return (
    <AutoComplete
      value={value}
      options={options}
      onSearch={(text) => setSearchText(text)}
      onSelect={(_val: string, option: { value: string; key: string; resource: ResourceItem }) => {
        onChange?.(option.value, option.resource);
      }}
      onChange={(text) => {
        // Allow free-form typing; clear resource context
        onChange?.(text);
      }}
      optionRender={(option) => {
        const item = results.find((r) => r.itcode === option.key);
        if (!item) return option.label;
        return (
          <div className="flex items-center justify-between">
            <span>
              <Text strong>{item.name}</Text>
              <Text type="secondary" className="ml-2">({item.itcode})</Text>
            </span>
            <Text type="secondary" className="text-xs">{item.email}</Text>
          </div>
        );
      }}
      placeholder={placeholder}
      disabled={disabled}
      style={style}
      allowClear
      className="w-full"
    />
  );
}
