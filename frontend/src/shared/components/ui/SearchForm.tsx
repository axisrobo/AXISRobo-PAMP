'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { Input, Select, DatePicker, Button, AutoComplete } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { useT } from '@/shared/lib/locale';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

export interface SearchField {
  key: string;
  label: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'combobox';
  placeholder?: string;
  options?: { label: string; value: string }[];
  showSearch?: boolean;
  /** For daterange: the query param key for start date (default: key + 'From') */
  fromKey?: string;
  /** For daterange: the query param key for end date (default: key + 'To') */
  toKey?: string;
}

type FormValues = Record<string, string | string[]>;

interface SearchFormProps {
  fields: SearchField[];
  initialValues?: Record<string, string>;
  onSearch: (values: Record<string, string>) => void;
  onReset: () => void;
  onChange?: (key: string, value: string | string[], allValues: Record<string, string>) => void;
  autoSearchFieldTypes?: SearchField['type'][];
  resetToInitialValues?: boolean;
  /** When true, pressing Enter in text inputs will NOT trigger a search */
  disableEnterSearch?: boolean;
  /** When true, renders all fields and buttons in a single horizontal row */
  inline?: boolean;
}

export function SearchForm({ fields, initialValues, onSearch, onReset, onChange, autoSearchFieldTypes = [], resetToInitialValues = false, disableEnterSearch = false, inline = false }: SearchFormProps) {
  const t = useT();

  // Stable serialisation of initialValues for dependency tracking
  const initialValuesKey = useMemo(
    () => JSON.stringify(initialValues ?? {}),
    [initialValues]
  );

  const buildFormValues = (iv?: Record<string, string>): FormValues => {
    const vals: FormValues = {};
    fields.forEach((f) => {
      if (f.type === 'multiselect') {
        vals[f.key] = iv?.[f.key] ? iv[f.key].split(',') : [];
      } else if (f.type === 'daterange') {
        const fk = f.fromKey || `${f.key}From`;
        const tk = f.toKey || `${f.key}To`;
        const from = iv?.[fk] ?? '';
        const to = iv?.[tk] ?? '';
        vals[f.key] = (from || to) ? `${from},${to}` : '';
      } else {
        vals[f.key] = iv?.[f.key] ?? '';
      }
    });
    return vals;
  };

  const [values, setValues] = useState<FormValues>(() => buildFormValues(initialValues));

  const flattenValues = (nextValues: FormValues): Record<string, string> => {
    const flat: Record<string, string> = {};
    for (const [k, v] of Object.entries(nextValues)) {
      const field = fields.find((f) => f.key === k);
      if (field?.type === 'daterange') {
        const raw = typeof v === 'string' ? v : '';
        const [from = '', to = ''] = raw.split(',');
        const fk = field.fromKey || `${k}From`;
        const tk = field.toKey || `${k}To`;
        if (from) flat[fk] = from;
        if (to) flat[tk] = to;
      } else {
        flat[k] = Array.isArray(v) ? v.join(',') : v;
      }
    }
    return flat;
  };

  // Sync form state when initialValues change (e.g. URL-derived filters)
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    setValues(buildFormValues(initialValues));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValuesKey]);

  const handleChange = (key: string, value: string | string[]) => {
    const nextValues = { ...values, [key]: value };
    setValues(nextValues);

    const flat = flattenValues(nextValues);
    if (onChange) {
      onChange(key, value, flat);
    }

    const field = fields.find((item) => item.key === key);
    if (field && autoSearchFieldTypes.includes(field.type)) {
      onSearch(flat);
    }
  };

  const handleSearch = () => {
    onSearch(flattenValues(values));
  };

  const handleReset = () => {
    if (resetToInitialValues) {
      setValues(buildFormValues(initialValues));
    } else {
      // Reset to empty defaults (not initialValues) so URL filters are cleared
      const empty: FormValues = {};
      fields.forEach((f) => {
        empty[f.key] = f.type === 'multiselect' ? [] : '';
      });
      setValues(empty);
    }
    onReset();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !disableEnterSearch) handleSearch();
  };

  if (inline) {
    return (
      <div className="flex flex-wrap items-end gap-2 px-4 py-3 border-b border-border-light">
        {fields.map((field) => (
          <div key={field.key} className="flex flex-col min-w-[160px] flex-1">
            <label className="block text-xs text-text-secondary mb-1">{t(field.label)}</label>
            {field.type === 'multiselect' ? (
              <Select
                mode="multiple"
                allowClear
                maxTagCount={2}
                style={{ width: '100%', height: 36 }}
                placeholder={field.placeholder || t('All')}
                value={Array.isArray(values[field.key]) ? values[field.key] as string[] : []}
                onChange={(selected) => handleChange(field.key, selected)}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
              />
            ) : field.type === 'select' ? (
              <Select
                allowClear
                style={{ width: '100%', height: 36 }}
                placeholder={t('All')}
                value={(values[field.key] as string) || undefined}
                onChange={(v) => handleChange(field.key, v ?? '')}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
                showSearch={field.showSearch}
                filterOption={field.showSearch ? (input, option) =>
                  String(option?.label ?? '').toLowerCase().includes(input.toLowerCase()) : undefined
                }
              />
            ) : field.type === 'combobox' ? (
              <AutoComplete
                style={{ width: '100%' }}
                placeholder={field.placeholder || `Select or type ${field.label}`}
                value={values[field.key] as string}
                onChange={(v) => handleChange(field.key, v)}
                onKeyDown={handleKeyDown}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
                filterOption={(input, option) =>
                  (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
                }
                className="h-9"
              />
            ) : field.type === 'daterange' ? (() => {
              const raw = typeof values[field.key] === 'string' ? (values[field.key] as string) : '';
              const [from, to] = raw ? raw.split(',') : ['', ''];
              const rangeValue: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null =
                from || to ? [from ? dayjs(from) : null, to ? dayjs(to) : null] : null;
              return (
                <RangePicker
                  style={{ width: '100%', height: 36 }}
                  value={rangeValue}
                  onChange={(_dates, dateStrs) => {
                    const [s, e] = dateStrs || ['', ''];
                    handleChange(field.key, (s || e) ? `${s},${e}` : '');
                  }}
                />
              );
            })() : field.type === 'date' ? (
              <DatePicker
                style={{ width: '100%', height: 36 }}
                value={(values[field.key] as string) ? dayjs(values[field.key] as string) : null}
                onChange={(_date, dateStr) => handleChange(field.key, (typeof dateStr === 'string' ? dateStr : (dateStr?.[0] ?? '')) || '')}
              />
            ) : (
              <input
                type="text"
                value={values[field.key] as string}
                onChange={(e) => handleChange(field.key, e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={field.placeholder || `Enter ${field.label}`}
                className="h-9 w-full rounded-md border border-[#d9d9d9] bg-white px-3 text-sm text-text-primary outline-none transition-colors placeholder:text-[#b5b5b5] focus:border-primary-blue"
              />
            )}
          </div>
        ))}
        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={handleSearch}
            className="inline-flex h-9 items-center justify-center rounded-md bg-primary-blue px-5 text-sm font-medium text-white transition-colors hover:bg-primary-blue-hover"
          >
            {t('Search')}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex h-9 items-center justify-center rounded-md border border-[#d9d9d9] bg-white px-5 text-sm font-medium text-[#595959] transition-colors hover:border-[#bfbfbf] hover:text-text-primary"
          >
            {t('Reset')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-border-light p-4 mb-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {fields.map((field) => (
          <div key={field.key}>
            <label className="block text-xs text-text-secondary mb-1">{t(field.label)}</label>
            {field.type === 'multiselect' ? (
              <Select
                mode="multiple"
                allowClear
                maxTagCount={2}
                style={{ width: '100%' }}
                placeholder={field.placeholder || t('All')}
                value={Array.isArray(values[field.key]) ? values[field.key] as string[] : []}
                onChange={(selected) => handleChange(field.key, selected)}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
                size="small"
              />
            ) : field.type === 'select' ? (
              <Select
                allowClear
                style={{ width: '100%' }}
                placeholder={t('All')}
                value={(values[field.key] as string) || undefined}
                onChange={(v) => handleChange(field.key, v ?? '')}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
                size="small"
                showSearch={field.showSearch}
                filterOption={field.showSearch ? (input, option) =>
                  String(option?.label ?? '').toLowerCase().includes(input.toLowerCase()) : undefined
                }
              />
            ) : field.type === 'combobox' ? (
              <AutoComplete
                style={{ width: '100%' }}
                placeholder={field.placeholder || `Select or type ${field.label}`}
                value={values[field.key] as string}
                onChange={(v) => handleChange(field.key, v)}
                onKeyDown={handleKeyDown}
                options={field.options?.map((o) => ({ label: o.label, value: o.value }))}
                filterOption={(input, option) =>
                  (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
                }
                size="small"
              />
            ) : field.type === 'daterange' ? (() => {
              const raw = typeof values[field.key] === 'string' ? (values[field.key] as string) : '';
              const [from, to] = raw ? raw.split(',') : ['', ''];
              const rangeValue: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null =
                from || to ? [from ? dayjs(from) : null, to ? dayjs(to) : null] : null;
              return (
                <RangePicker
                  style={{ width: '100%' }}
                  value={rangeValue}
                  onChange={(_dates, dateStrs) => {
                    const [s, e] = dateStrs || ['', ''];
                    handleChange(field.key, (s || e) ? `${s},${e}` : '');
                  }}
                  size="small"
                />
              );
            })() : field.type === 'date' ? (
              <DatePicker
                style={{ width: '100%' }}
                value={(values[field.key] as string) ? dayjs(values[field.key] as string) : null}
                onChange={(_date, dateStr) => handleChange(field.key, (typeof dateStr === 'string' ? dateStr : (dateStr?.[0] ?? '')) || '')}
                size="small"
              />
            ) : (
              <Input
                value={values[field.key] as string}
                onChange={(e) => handleChange(field.key, e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={field.placeholder || `Enter ${field.label}`}
                size="small"
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-3">
        <Button type="primary" size="small" icon={<SearchOutlined />} onClick={handleSearch}>
          {t('Search')}
        </Button>
        <Button size="small" icon={<ReloadOutlined />} onClick={handleReset}>
          {t('Reset')}
        </Button>
      </div>
    </div>
  );
}
