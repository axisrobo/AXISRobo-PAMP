'use client';

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { api } from '@/shared/lib/api';
import { RichTextEditor } from '@/shared/components/ui/RichTextEditor';

// ── Options ──────────────────────────────────────────────────────────────────

export const CATEGORY_OPTIONS = [
  'OS', 'Runtime Technologies', 'Storage', 'Database Technology',
  'Integration', 'Network', 'Security', 'Application', 'Framework',
  'Library', 'Platform', 'Language', 'Tool',
].map(v => ({ label: v, value: v }));

export const SUB_CATEGORY_OPTIONS = [
  'Gen AI', 'Frontend', 'Backend', 'Logging', 'Security', 'Cloud', 'DevOps',
].map(v => ({ label: v, value: v }));

export const EA_ADVICE_OPTIONS = [
  { label: 'Prohibited', value: 'Prohibited' },
  { label: 'Accepted', value: 'Accepted' },
  { label: 'Expected', value: 'Expected' },
];

export const YES_NO_OPTIONS = [
  { label: 'Yes', value: 'Yes' },
  { label: 'No', value: 'No' },
];

export const SOURCE_TYPE_OPTIONS = [
  'Cloud Managed',
  'Open Source',
  'Commercial',
  'Vendor Hardware',
  'SaaS',
  'Standard / Protocol',
  'Internal',
].map(v => ({ label: v, value: v }));

export const SECURITY_RISK_OPTIONS = [
  { label: 'Very Critical', value: 'Very Critical' },
  { label: 'Critical', value: 'Critical' },
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
  { label: 'No', value: 'No' },
];

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MasterRecord {
  id?: string;
  masterNo?: number;
  category: string;
  sourceType?: string;
  source?: string;
  subCategory?: string;
  component: string;
  componentPackage: string;
  version?: string;
  majorVersion?: number;
  minorVersion?: string;
  patchVersion?: string;
  eaAdvice: string;
  standard?: string;
  restricted?: string;
  remark?: string;
  initialReleaseDate?: string;
  finalReleaseDate?: string;
  eolDate?: string;
  securityVulnerability?: string;
  securityServerity?: string;
  cvssV3Score?: number | string;
  securityAdvice?: string;
  vulnerabilityLink?: string;
  status?: string;
  createdBy?: string;
  createdAt?: string;
}

// ── Field helpers ─────────────────────────────────────────────────────────────

function FormField({
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
      <label className="text-sm text-text-secondary">
        {required && <span className="text-red-500 mr-0.5">*</span>}
        {label}
      </label>
      {children}
      {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
    </div>
  );
}

const inputCls =
  'w-full border border-border-default rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary-blue bg-white';
const selectCls =
  'w-full border border-border-default rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary-blue bg-white';

// ── Main component ────────────────────────────────────────────────────────────

interface Props {
  /** Provide initial values when editing an existing record */
  initialValues?: Partial<MasterRecord>;
  /** The id of the record to update; undefined means "create new" */
  recordId?: string;
}

export default function MasterDataForm({ initialValues, recordId }: Props) {
  const router = useRouter();
  const isEdit = !!recordId;

  const [form, setForm] = useState<Partial<MasterRecord>>(initialValues ?? {});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  type CategoryOption = { label: string; value: string };

  const { data: categoryData } = useQuery({
    queryKey: ['techStackCategoryOptions'],
    queryFn: () => api.get<any>('/technology-stack/categories'),
  });

  const categoryOptions: CategoryOption[] = useMemo(
    () => (categoryData?.categories ?? []).map((o: any) => ({ label: String(o.label), value: String(o.value) })),
    [categoryData]
  );

  const subCategoryOptions = useMemo(() => {
    const all = (categoryData?.subCategories ?? []) as Array<{ category: string; label: string; value: string }>;
    if (!form.category) {
      return [];
    }
    return all
      .filter((o) => o.category === form.category)
      .map((o) => ({ label: o.label, value: o.value }));
  }, [categoryData, form.category]);

  const set = (field: keyof MasterRecord, value: string | number | undefined) =>
    setForm(prev => ({ ...prev, [field]: value }));

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
    if (!form.category) errs.category = 'Required';
    if (!form.subCategory) errs.subCategory = 'Required';
    if (!form.component) errs.component = 'Required';
    if (!form.componentPackage) errs.componentPackage = 'Required';
    if (!form.standard) errs.standard = 'Required';
    if (form.majorVersion === undefined || form.majorVersion === null) {
      errs.majorVersion = 'Required';
    }
    if (form.minorVersion && form.minorVersion.length > 30) {
      errs.minorVersion = 'Max length is 30 characters';
    }
    if (!form.eaAdvice) errs.eaAdvice = 'Required';

    const initial = parseDate(form.initialReleaseDate);
    const final = parseDate(form.finalReleaseDate);
    const eol = parseDate(form.eolDate);

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
        await api.put(`/technology-stack/${recordId}`, buildPayload(form));
      } else {
        await api.post('/technology-stack', buildPayload(form));
      }
      router.push('/tech-stack/master-data');
    } catch {
      setErrors(prev => ({ ...prev, _global: 'Save failed. Please try again.' }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          className="flex items-center justify-center w-8 h-8 rounded hover:bg-gray-100 text-text-secondary"
          onClick={() => router.push('/tech-stack/master-data')}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h1 className="text-lg font-semibold text-text-primary">
          {isEdit ? 'Edit Master Data' : 'New Master Data'}
        </h1>
      </div>

      {/* Card */}
      <div className="bg-white border border-border-light rounded-lg p-6">
        {errors._global && (
          <p className="text-sm text-red-500 mb-4">{errors._global}</p>
        )}

        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {/* Category */}
          <FormField label="Category" required error={errors.category}>
            <select
              className={selectCls}
              value={form.category ?? ''}
              onChange={e => {
                set('category', e.target.value);
                set('subCategory', undefined);
              }}
            >
              <option value="">-- Select --</option>
              {categoryOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          
          {/* Sub Category */}
          <FormField label="Sub Category" required error={errors.subCategory}>
            <select
              className={selectCls}
              value={form.subCategory ?? ''}
              onChange={e => set('subCategory', e.target.value)}
              disabled={!form.category}
            >
              <option value="">-- Select --</option>
              {subCategoryOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          {/* Initial Release Date */}
          <FormField label="Initial Release Date" error={errors.initialReleaseDate}>
            <input type="date" className={inputCls} value={form.initialReleaseDate ?? ''} onChange={e => set('initialReleaseDate', e.target.value)} />
          </FormField>

          <FormField label="Source Type">
            <select
              className={selectCls}
              value={form.sourceType ?? ''}
              onChange={e => set('sourceType', e.target.value || undefined)}
            >
              <option value="">-- Select --</option>
              {SOURCE_TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          <FormField label="Source">
            <input
              className={inputCls}
              value={form.source ?? ''}
              onChange={e => set('source', e.target.value || undefined)}
              placeholder="Please input source"
            />
          </FormField>

          {/* Final Release Date */}
          <FormField label="Final Release Date" error={errors.finalReleaseDate}>
            <input type="date" className={inputCls} value={form.finalReleaseDate ?? ''} onChange={e => set('finalReleaseDate', e.target.value)} />
          </FormField>

          {/* Technology Component */}
          <FormField label="Technology Component" required error={errors.component}>
            <input className={inputCls} value={form.component ?? ''} onChange={e => set('component', e.target.value)} placeholder="e.g. React" />
          </FormField>

          {/* EOL Date */}
          <FormField label="EOL Date" error={errors.eolDate}>
            <input type="date" className={inputCls} value={form.eolDate ?? ''} onChange={e => set('eolDate', e.target.value)} />
          </FormField>

          {/* Component Package Name */}
          <FormField label="Component Package Name" required error={errors.componentPackage}>
            <input className={inputCls} value={form.componentPackage ?? ''} onChange={e => set('componentPackage', e.target.value)} placeholder="e.g. react" />
          </FormField>

          {/* Security Advice */}
          <FormField label="Security Advice">
            <select className={selectCls} value={form.securityServerity ?? ''} onChange={e => set('securityServerity', e.target.value)}>
              <option value="">-- Select --</option>
              {SECURITY_RISK_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          {/* Standard */}
          <FormField label="Standard" required error={errors.standard}>
            <select className={selectCls} value={form.standard ?? ''} onChange={e => set('standard', e.target.value)}>
              <option value="">-- Select --</option>
              {YES_NO_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          {/* CVSS v3 Score */}
          <FormField label="CVSS v3 Score">
            <input
              type="number"
              step="0.1"
              className={inputCls}
              value={form.cvssV3Score ?? ''}
              onChange={e => set('cvssV3Score', e.target.value ? Number(e.target.value) : undefined)}
              placeholder="e.g. 7.5"
            />
          </FormField>

          {/* Restricted */}
          <FormField label="Restricted">
            <select className={selectCls} value={form.restricted ?? ''} onChange={e => set('restricted', e.target.value)}>
              <option value="">-- Select --</option>
              {YES_NO_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          {/* Major Version */}
          <FormField label="Major Version" required error={errors.majorVersion}>
            <input
              type="number"
              className={inputCls}
              value={form.majorVersion ?? ''}
              onChange={e => set('majorVersion', e.target.value === '' ? undefined : Number(e.target.value))}
              placeholder="18"
            />
          </FormField>

          {/* Vulnerability Link */}
          <FormField label="Vulnerability Link">
            <input className={inputCls} value={form.vulnerabilityLink ?? ''} onChange={e => set('vulnerabilityLink', e.target.value)} placeholder="https://..." />
          </FormField>

          {/* Minor Version */}
          <FormField label="Minor Version">
            <input
              className={inputCls}
              value={form.minorVersion ?? ''}
              maxLength={30}
              onChange={e => set('minorVersion', e.target.value || undefined)}
              placeholder="0"
            />
          </FormField>

          {/* EA Advice */}
          <FormField label="EA Advice" required error={errors.eaAdvice}>
            <select className={selectCls} value={form.eaAdvice ?? ''} onChange={e => set('eaAdvice', e.target.value)}>
              <option value="">-- Select --</option>
              {EA_ADVICE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </FormField>

          {/* Patch Version */}
          <FormField label="Patch Version">
            <input className={inputCls} value={form.patchVersion ?? ''} onChange={e => set('patchVersion', e.target.value)} placeholder="0" />
          </FormField>

          {/* Security Vulnerability — full width */}
          <FormField label="Security Vulnerability" fullWidth>
            <RichTextEditor
              value={form.securityVulnerability ?? ''}
              onChange={html => set('securityVulnerability', html)}
              placeholder="Please Input Text"
              minHeight={160}
            />
          </FormField>

          {/* Remark — full width */}
          <FormField label="Remark" fullWidth>
            <textarea
              className={`${inputCls} resize-none`}
              rows={3}
              value={form.remark ?? ''}
              onChange={e => set('remark', e.target.value)}
              placeholder="Optional remarks"
            />
          </FormField>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-border-default">
          <button
            className="px-4 py-2 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary"
            onClick={() => router.push('/tech-stack/master-data')}
            disabled={saving}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 text-sm bg-primary-blue text-white rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
