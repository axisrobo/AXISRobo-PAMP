/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft } from 'lucide-react';
import { Button, Select, Input, DatePicker } from 'antd';
import dayjs from 'dayjs';
import { api } from '@/shared/lib/api';
import { RichTextEditor } from '@/shared/components/ui/RichTextEditor';
import {
  EA_ADVICE_OPTIONS,
  YES_NO_OPTIONS,
  SECURITY_RISK_OPTIONS,
  SOURCE_TYPE_OPTIONS,
  MasterRecord,
} from './MasterDataForm';

interface Props {
  recordId?: string; // undefined = new, string = edit
  onClose: () => void;
  onSaved: () => void;
}

function Field({
  label,
  required,
  error,
  children,
  fullWidth,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <div className={`flex flex-col gap-1 ${fullWidth ? 'col-span-2' : ''}`}>
      <label className="text-sm text-gray-500">
        {required && <span className="text-red-500 mr-0.5">*</span>}
        {label}
      </label>
      {children}
      {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
    </div>
  );
}

export function MasterDataDrawer({ recordId, onClose, onSaved }: Props) {
  const isEdit = !!recordId;

  // Fetch existing record when editing
  const { data: existing, isLoading } = useQuery<MasterRecord>({
    queryKey: ['techStackMasterOne', recordId],
    queryFn: () => api.get<MasterRecord>(`/technology-stack/${recordId}`),
    enabled: isEdit,
  });

  const [form, setForm] = useState<Partial<MasterRecord>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const { data: categoryData } = useQuery({
    queryKey: ['techStackCategoryOptions'],
    queryFn: () => api.get<any>('/technology-stack/categories'),
  });

  // Merge fetched data into form state once loaded
  const initialised = !isEdit || !!existing;
  const formData: Partial<MasterRecord> = isEdit
    ? { ...existing, ...form }
    : form;

  const categoryOptions = (categoryData?.categories ?? []).map((o: any) => ({ label: o.label, value: o.value }));
  const subCategoryOptions = ((categoryData?.subCategories ?? []) as Array<{ category: string; label: string; value: string }>)
    .filter((o) => !!formData.category && o.category === formData.category)
    .map((o) => ({ label: o.label, value: o.value }));

  const set = (field: keyof MasterRecord, value: any) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const buildPayload = (data: Partial<MasterRecord>) => {
    const { version: _version, ...payload } = data;
    return payload;
  };

  const parseDate = (value?: string) => {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formData.category) errs.category = 'Required';
    if (!formData.subCategory) errs.subCategory = 'Required';
    if (!formData.component) errs.component = 'Required';
    if (!formData.componentPackage) errs.componentPackage = 'Required';
    if (!formData.standard) errs.standard = 'Required';
    if (formData.majorVersion === undefined || formData.majorVersion === null) {
      errs.majorVersion = 'Required';
    }
    if (formData.minorVersion && String(formData.minorVersion).length > 30) {
      errs.minorVersion = 'Max length is 30 characters';
    }
    if (!formData.eaAdvice) errs.eaAdvice = 'Required';

    const initial = parseDate(formData.initialReleaseDate);
    const final = parseDate(formData.finalReleaseDate);
    const eol = parseDate(formData.eolDate);

    if (initial && final && initial > final) {
      errs.initialReleaseDate = 'Must be <= Final Release Date';
      errs.finalReleaseDate = 'Must be >= Initial Release Date';
    }
    if (final && eol && final > eol) {
      errs.finalReleaseDate = 'Must be <= EOL Date';
      errs.eolDate = 'Must be >= Final Release Date';
    }
    if (initial && eol && initial > eol) {
      errs.initialReleaseDate = 'Must be <= EOL Date';
      errs.eolDate = 'Must be >= Initial Release Date';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await api.put(`/technology-stack/${recordId}`, buildPayload(formData));
      } else {
        await api.post('/technology-stack', buildPayload(formData));
      }
      onSaved();
    } catch {
      setErrors((prev) => ({ ...prev, _global: 'Save failed. Please try again.' }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40" role="dialog" aria-modal="true" aria-label={isEdit ? 'Edit Master Data' : 'New Master Data'}>
      <div className="absolute right-0 top-0 h-full w-[1100px] max-w-full bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b shrink-0">
          <button
            onClick={onClose}
            className="flex items-center text-gray-500 hover:text-gray-700 shrink-0"
            aria-label="Close"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-base font-semibold text-gray-800 flex-1">
            {isEdit ? 'Edit Master Data' : 'New Master Data'}
          </h2>
          <div className="flex items-center gap-3">
            {errors._global && (
              <p className="text-sm text-red-500">{errors._global}</p>
            )}
            <Button onClick={onClose}>Cancel</Button>
            <Button
              type="primary"
              onClick={handleSave}
              loading={saving}
              disabled={!initialised}
            >
              Save
            </Button>
          </div>
        </div>

        {/* Body */}
        {!initialised ? (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Loading...
          </div>
        ) : isLoading && isEdit ? (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Loading...
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto px-8 py-6">
            <div className="grid grid-cols-2 gap-x-8 gap-y-4">

              <Field label="Category" required error={errors.category}>
                <Select
                  className="w-full"
                  status={errors.category ? 'error' : undefined}
                  value={formData.category || undefined}
                  onChange={(v) => {
                    set('category', v ?? '');
                    set('subCategory', '');
                  }}
                  placeholder="-- Select --"
                  allowClear
                  options={categoryOptions}
                />
              </Field>

              <Field label="Sub Category" required error={errors.subCategory}>
                <Select
                  className="w-full"
                  status={errors.subCategory ? 'error' : undefined}
                  value={formData.subCategory || undefined}
                  onChange={(v) => set('subCategory', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  disabled={!formData.category}
                  options={subCategoryOptions}
                />
              </Field>

              <Field label="Technology Component" required error={errors.component}>
                <Input
                  status={errors.component ? 'error' : undefined}
                  value={formData.component ?? ''}
                  onChange={(e) => set('component', e.target.value)}
                  placeholder="e.g. React"
                />
              </Field>

              <Field label="Initial Release Date" error={errors.initialReleaseDate}>
                <DatePicker
                  className="w-full"
                  value={formData.initialReleaseDate ? dayjs(formData.initialReleaseDate) : null}
                  onChange={(d) => set('initialReleaseDate', d ? d.format('YYYY-MM-DD') : '')}
                />
              </Field>

              <Field label="Component Package Name" required error={errors.componentPackage}>
                <Input
                  status={errors.componentPackage ? 'error' : undefined}
                  value={formData.componentPackage ?? ''}
                  onChange={(e) => set('componentPackage', e.target.value)}
                  placeholder="e.g. react"
                />
              </Field>

              <Field label="Final Release Date" error={errors.finalReleaseDate}>
                <DatePicker
                  className="w-full"
                  value={formData.finalReleaseDate ? dayjs(formData.finalReleaseDate) : null}
                  onChange={(d) => set('finalReleaseDate', d ? d.format('YYYY-MM-DD') : '')}
                />
              </Field>


              <Field label="Source Type">
                <Select
                  className="w-full"
                  value={formData.sourceType || undefined}
                  onChange={(v) => set('sourceType', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  options={SOURCE_TYPE_OPTIONS}
                />
              </Field>

              <Field label="EOL Date" error={errors.eolDate}>
                <DatePicker
                  className="w-full"
                  value={formData.eolDate ? dayjs(formData.eolDate) : null}
                  onChange={(d) => set('eolDate', d ? d.format('YYYY-MM-DD') : '')}
                />
              </Field>

              <Field label="Source">
                <Input
                  value={formData.source ?? ''}
                  onChange={(e) => set('source', e.target.value)}
                  placeholder="Please input source"
                />
              </Field>

              <Field label="Security Advice">
                <Select
                  className="w-full"
                  value={formData.securityServerity || undefined}
                  onChange={(v) => set('securityServerity', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  options={SECURITY_RISK_OPTIONS}
                />
              </Field>

              <Field label="Standard" required error={errors.standard}>
                <Select
                  className="w-full"
                  status={errors.standard ? 'error' : undefined}
                  value={formData.standard || undefined}
                  onChange={(v) => set('standard', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  options={YES_NO_OPTIONS}
                />
              </Field>

              <Field label="CVSS v3 Score">
                <Input
                  type="number"
                  value={formData.cvssV3Score ?? ''}
                  onChange={(e) =>
                    set('cvssV3Score', e.target.value ? Number(e.target.value) : undefined)
                  }
                  placeholder="e.g. 7.5"
                />
              </Field>

              <Field label="Restricted">
                <Select
                  className="w-full"
                  value={formData.restricted || undefined}
                  onChange={(v) => set('restricted', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  options={YES_NO_OPTIONS}
                />
              </Field>

              <Field label="Major Version" required error={errors.majorVersion}>
                <Input
                  type="number"
                  status={errors.majorVersion ? 'error' : undefined}
                  value={formData.majorVersion ?? ''}
                  onChange={(e) =>
                    set('majorVersion', e.target.value === '' ? undefined : Number(e.target.value))
                  }
                  placeholder="18"
                />
              </Field>

              <Field label="Vulnerability Link">
                <Input
                  value={formData.vulnerabilityLink ?? ''}
                  onChange={(e) => set('vulnerabilityLink', e.target.value)}
                  placeholder="https://..."
                />
              </Field>

              <Field label="Minor Version">
                <Input
                  value={formData.minorVersion ?? ''}
                  maxLength={30}
                  status={errors.minorVersion ? 'error' : undefined}
                  onChange={(e) =>
                    set('minorVersion', e.target.value || undefined)
                  }
                  placeholder="0"
                />
              </Field>

              <Field label="EA Advice" required error={errors.eaAdvice}>
                <Select
                  className="w-full"
                  status={errors.eaAdvice ? 'error' : undefined}
                  value={formData.eaAdvice || undefined}
                  onChange={(v) => set('eaAdvice', v ?? '')}
                  placeholder="-- Select --"
                  allowClear
                  options={EA_ADVICE_OPTIONS}
                />
              </Field>

              <Field label="Patch Version">
                <Input
                  value={formData.patchVersion ?? ''}
                  onChange={(e) => set('patchVersion', e.target.value)}
                  placeholder="0"
                />
              </Field>

              <Field label="Security Vulnerability" fullWidth>
                <RichTextEditor
                  value={formData.securityVulnerability ?? ''}
                  onChange={(html) => set('securityVulnerability', html)}
                  placeholder="Please Input Text"
                  minHeight={160}
                />
              </Field>

              <Field label="Remark" fullWidth>
                <Input.TextArea
                  rows={3}
                  value={formData.remark ?? ''}
                  onChange={(e) => set('remark', e.target.value)}
                  placeholder="Optional remarks"
                />
              </Field>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
