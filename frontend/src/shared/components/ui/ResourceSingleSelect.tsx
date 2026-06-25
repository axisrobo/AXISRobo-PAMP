'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Select, Spin } from 'antd';
import { api } from '@/shared/lib/api';

interface ResourceOption {
  key: string;
  value: string;
  itcode: string;
  name: string;
  email?: string;
}

interface ResourceSingleSelectProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  limit?: number;
}

export function ResourceSingleSelect({
  value,
  onChange,
  placeholder = 'Search by IT code or name',
  className,
  limit = 100,
}: ResourceSingleSelectProps) {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data = [], isFetching } = useQuery<ResourceOption[]>({
    queryKey: ['resourceSingleSelect', debouncedSearch, limit],
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

    const fallback =
      value && !remoteOptions.some((opt) => opt.value === value)
        ? [{ key: value, value, label: value, title: value }]
        : [];

    return [...fallback, ...remoteOptions];
  }, [data, value]);

  return (
    <Select
      showSearch
      allowClear
      value={value || undefined}
      onChange={(val) => onChange(val ?? '')}
      onSearch={setSearch}
      placeholder={placeholder}
      className={className}
      style={{ width: '100%' }}
      filterOption={false}
      options={options}
      optionLabelProp="value"
      notFoundContent={
        isFetching ? (
          <Spin size="small" />
        ) : debouncedSearch ? (
          'No matching resources'
        ) : (
          'Type to search'
        )
      }
    />
  );
}
