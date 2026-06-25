/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft } from 'lucide-react';
import { Input, Select, Button } from 'antd';
import { api } from '@/shared/lib/api';
import { RiskLevelBadge } from '@/shared/components/ui/RiskLevelBadge';

const USE_STATUS_OPTIONS = ['Used', 'Deprecated'];
const VERSION_NUMBERS = Array.from({ length: 50 }, (_, i) => i);
const EA_ADVICE_OPTIONS = ['Prohibited', 'Accepted', 'Expected'];
const SECURITY_ADVICE_OPTIONS = ['Very Critical', 'Critical', 'High', 'Medium', 'Low', 'No'];

interface CatalogItemModalProps {
  appId: string;
  item?: any;                        // defined = edit mode, undefined = add mode
  onClose: () => void;
  onSaved: () => void;
}

export function CatalogItemModal({ appId, item, onClose, onSaved }: CatalogItemModalProps) {
  const isEdit = !!item;

  const [form, setForm] = useState({
    category: item?.category ?? '',
    subCategory: item?.subCategory ?? '',
    component: item?.component ?? '',
    componentPackage: item?.componentPackage ?? '',
    eaAdvice: item?.eaAdvice ?? '',
    securityAdvice: item?.securityAdvice ?? '',
    majorVersion: item?.majorVersion ?? '',
    minorVersion: item?.minorVersion ?? '',
    patchVersion: item?.patchVersion ?? '',
    useStatus: item?.useStatus ?? '',
    statusComments: item?.statusComments ?? '',
    remark: item?.remark ?? '',
    // from master data lookup (read-only)
    eolDate: item?.eolDate ?? '',
    eolIntervalTime: item?.eolIntervalTime ?? '',
    maintainabilityRiskLevel: item?.maintainabilityRiskLevel ?? '',
    securityRiskLevel: item?.securityRiskLevel ?? '',
    cvssV3Score: item?.cvssV3Score ?? '',
    standard: item?.standard ?? '',
    masterNo: item?.masterNo ?? '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const { data: categoryData } = useQuery({
    queryKey: ['techStackCategoryOptions'],
    queryFn: () => api.get<any>('/technology-stack/categories'),
  });

  const categoryOptions = useMemo(
    () => (categoryData?.categories ?? []).map((o: any) => ({ label: o.label, value: o.value })),
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

  const { data: masterOptionsData, isFetching: masterOptionsLoading } = useQuery({
    queryKey: ['techStackMasterOptions', form.category, form.subCategory],
    queryFn: () =>
      api.get<any>('/technology-stack/master-options', {
        category: form.category,
        subCategory: form.subCategory,
      }),
    enabled: !!form.category && !!form.subCategory,
  });

  const componentOptions = useMemo(
    () => (masterOptionsData?.components ?? []).map((o: any) => ({ label: o.label, value: o.value })),
    [masterOptionsData]
  );

  const componentPackageOptions = useMemo(() => {
    const byComponent = (masterOptionsData?.componentPackagesByComponent ?? {}) as Record<string, string[]>;
    if (form.component && byComponent[form.component]) {
      return byComponent[form.component].map((v) => ({ label: v, value: v }));
    }
    return (masterOptionsData?.componentPackages ?? []).map((o: any) => ({ label: o.label, value: o.value }));
  }, [masterOptionsData, form.component]);

  useEffect(() => {
    if (!form.subCategory) return;
    const valid = subCategoryOptions.some((o) => o.value === form.subCategory);
    if (!valid) {
      set('subCategory', '');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.subCategory, subCategoryOptions]);

  useEffect(() => {
    if (!form.component) return;
    const keepInitialEditValue = isEdit && item?.component === form.component;
    if (keepInitialEditValue) return;
    const valid = componentOptions.some((o: { label: string; value: string }) => o.value === form.component);
    if (!valid) {
      set('component', '');
      set('componentPackage', '');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.component, componentOptions]);

  useEffect(() => {
    if (!form.componentPackage) return;
    const keepInitialEditValue = isEdit && item?.componentPackage === form.componentPackage;
    if (keepInitialEditValue) return;
    const valid = componentPackageOptions.some((o: { label: string; value: string }) => o.value === form.componentPackage);
    if (!valid) {
      set('componentPackage', '');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.componentPackage, componentPackageOptions]);

  useEffect(() => {
    const { category, subCategory, component, componentPackage } = form;
    if (!category || !component || !componentPackage) {
      setForm((prev) => ({
        ...prev,
        eaAdvice: '',
        securityAdvice: '',
      }));
      return;
    }

    const params = new URLSearchParams({
      category,
      ...(subCategory && { subCategory }),
      component,
      componentPackage,
    });

    api.get<any>(`/technology-stack?${params.toString()}`).then((data) => {
      const rows: any[] = data?.data ?? [];
      const firstMatch = rows[0];
      setForm((prev) => ({
        ...prev,
        eaAdvice: firstMatch?.eaAdvice ?? '',
        securityAdvice: firstMatch?.securityServerity ?? firstMatch?.securityAdvice ?? '',
      }));
    }).catch(() => {
      setForm((prev) => ({
        ...prev,
        eaAdvice: '',
        securityAdvice: '',
      }));
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.category, form.subCategory, form.component, form.componentPackage]);

  // Auto-lookup master data when version fields change
  useEffect(() => {
    const { category, subCategory, component, componentPackage, majorVersion, minorVersion } = form;
    if (!category || !component || !componentPackage || majorVersion === '' || minorVersion === '') return;

    const params = new URLSearchParams({
      category,
      ...(subCategory && { subCategory }),
      component,
      componentPackage,
    });

    api.get<any>(`/technology-stack?${params.toString()}`).then((data) => {
      const rows: any[] = data?.data ?? [];
      const match = rows.find(
        (r) =>
          String(r.majorVersion) === String(majorVersion) &&
          String(r.minorVersion) === String(minorVersion)
      );
      if (match) {
        setForm((prev) => ({
          ...prev,
          eaAdvice: match.eaAdvice ?? '',
          securityAdvice: match.securityServerity ?? match.securityAdvice ?? '',
          eolDate: match.eolDate ?? '',
          eolIntervalTime: match.eolIntervalTime ?? '',
          maintainabilityRiskLevel: match.maintainabilityRiskLevel ?? '',
          securityRiskLevel: match.securityRiskLevel ?? '',
          cvssV3Score: match.cvssV3Score ?? '',
          standard: match.standard ?? '',
          masterNo: match.masterNo ?? '',
        }));
      } else {
        setForm((prev) => ({
          ...prev,
          eaAdvice: '',
          securityAdvice: '',
          eolDate: '',
          eolIntervalTime: '',
          maintainabilityRiskLevel: '',
          securityRiskLevel: '',
          cvssV3Score: '',
          standard: '',
          masterNo: '',
        }));
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.category, form.subCategory, form.component, form.componentPackage, form.majorVersion, form.minorVersion]);

  function set(key: string, value: any) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => { const next = { ...prev }; delete next[key]; return next; });
  }

  function validate(): boolean {
    const e: Record<string, string> = {};
    if (!form.category) e.category = 'Required';
    if (!form.subCategory) e.subCategory = 'Required';
    if (!form.component) e.component = 'Required';
    if (!form.componentPackage) e.componentPackage = 'Required';
    if (form.majorVersion === '' || form.majorVersion === null) e.majorVersion = 'Required';
    if (form.minorVersion === '' || form.minorVersion === null) e.minorVersion = 'Required';
    if (form.minorVersion && String(form.minorVersion).length > 30) {
      e.minorVersion = 'Max length is 30 characters';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = {
        category: form.category,
        subCategory: form.subCategory,
        component: form.component,
        componentPackage: form.componentPackage,
        eaAdvice: form.eaAdvice || undefined,
        securityAdvice: form.securityAdvice || undefined,
        majorVersion: Number(form.majorVersion),
        minorVersion: String(form.minorVersion),
        patchVersion: form.patchVersion || undefined,
        useStatus: form.useStatus || undefined,
        statusComments: form.statusComments || undefined,
        remark: form.remark || undefined,
        eolDate: form.eolDate || undefined,
        eolIntervalTime: form.eolIntervalTime || undefined,
        maintainabilityRiskLevel: form.maintainabilityRiskLevel || undefined,
        securityRiskLevel: form.securityRiskLevel || undefined,
        cvssV3Score: form.cvssV3Score !== '' ? Number(form.cvssV3Score) : undefined,
        standard: form.standard || undefined,
        masterNo: form.masterNo !== '' ? Number(form.masterNo) : undefined,
      };

      if (isEdit) {
        await api.put<any>(`/technology-stack/apps/${appId}/catalog/${item.id}`, payload);
      } else {
        await api.post<any>(`/technology-stack/apps/${appId}/catalog`, payload);
      }
      onSaved();
      onClose();
    } catch (err: any) {
      setErrors({ _global: err?.message ?? 'Save failed' });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[60] bg-black/20" role="dialog" aria-modal="true" aria-label="Key Technology Stack Catalog">
      <div className="absolute right-0 top-0 h-full w-[1100px] max-w-full bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 px-6 py-4 border-b">
          <button onClick={onClose} className="flex items-center text-gray-500 hover:text-gray-700 shrink-0" aria-label="Close">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-base font-semibold text-gray-800 flex-1">Key Technology Stack Catalog</h2>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 grid grid-cols-2 gap-x-8 gap-y-4">
          {/* Left column */}
          <div className="space-y-4">
            <Field label="Category" required error={errors.category}>
              <Select
                className="w-full"
                status={errors.category ? 'error' : undefined}
                value={form.category || undefined}
                onChange={(v) => {
                  set('category', v ?? '');
                  set('subCategory', '');
                  set('component', '');
                  set('componentPackage', '');
                }}
                placeholder="Please select"
                allowClear
                options={categoryOptions}
              />
            </Field>

            <Field label="Sub Category" required error={errors.subCategory}>
              <Select
                className="w-full"
                status={errors.subCategory ? 'error' : undefined}
                value={form.subCategory || undefined}
                onChange={(v) => {
                  set('subCategory', v ?? '');
                  set('component', '');
                  set('componentPackage', '');
                }}
                placeholder="Please select"
                allowClear
                disabled={!form.category}
                options={subCategoryOptions}
              />
            </Field>

            <Field label="Technology Component" required error={errors.component}>
              <Select
                className="w-full"
                status={errors.component ? 'error' : undefined}
                value={form.component || undefined}
                onChange={(v) => {
                  set('component', v ?? '');
                  set('componentPackage', '');
                }}
                placeholder="Please select"
                allowClear
                loading={masterOptionsLoading}
                disabled={!form.category || !form.subCategory}
                options={componentOptions}
              />
            </Field>

            <Field label="Component Package Name" required error={errors.componentPackage}>
              <Select
                className="w-full"
                status={errors.componentPackage ? 'error' : undefined}
                value={form.componentPackage || undefined}
                onChange={(v) => set('componentPackage', v ?? '')}
                placeholder="Please select"
                allowClear
                loading={masterOptionsLoading}
                disabled={!form.component}
                options={componentPackageOptions}
              />
            </Field>

            <Field label="Major Version" required error={errors.majorVersion}>
              <Select
                className="w-full"
                status={errors.majorVersion ? 'error' : undefined}
                value={form.majorVersion !== '' ? Number(form.majorVersion) : undefined}
                onChange={(v) => set('majorVersion', v ?? '')}
                placeholder="Please select"
                allowClear
                options={VERSION_NUMBERS.map(n => ({ label: String(n), value: n }))}
              />
            </Field>

            <Field label="Minor Version" required error={errors.minorVersion}>
              <Input
                status={errors.minorVersion ? 'error' : undefined}
                value={form.minorVersion ?? ''}
                onChange={(e) => set('minorVersion', e.target.value)}
                maxLength={30}
                placeholder="Please input"
              />
            </Field>

            <Field label="Patch Version">
              <Input
                value={form.patchVersion}
                onChange={(e) => set('patchVersion', e.target.value)}
              />
            </Field>

            <Field label="Comments">
              <Input
                value={form.statusComments}
                onChange={(e) => set('statusComments', e.target.value)}
              />
            </Field>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            <Field label="Use Status">
              <Select
                className="w-full"
                value={form.useStatus || undefined}
                onChange={(v) => set('useStatus', v ?? '')}
                placeholder="Please select"
                allowClear
                options={USE_STATUS_OPTIONS.map(o => ({ label: o, value: o }))}
              />
            </Field>

            <Field label="EA Advice">
              <Select
                className="w-full"
                value={form.eaAdvice || undefined}
                onChange={(v) => set('eaAdvice', v ?? '')}
                placeholder="Please select"
                allowClear
                options={EA_ADVICE_OPTIONS.map((o) => ({ label: o, value: o }))}
              />
            </Field>

            <Field label="Security Advice">
              <Select
                className="w-full"
                value={form.securityAdvice || undefined}
                onChange={(v) => set('securityAdvice', v ?? '')}
                placeholder="Please select"
                allowClear
                options={SECURITY_ADVICE_OPTIONS.map((o) => ({ label: o, value: o }))}
              />
            </Field>

            <Field label="Standard">
              <Input value={form.standard} readOnly className="bg-gray-50" />
            </Field>

            <Field label="EOL Date">
              <Input value={form.eolDate ? String(form.eolDate).slice(0, 10) : ''} readOnly className="bg-gray-50" />
            </Field>

            <Field label="EOL Interval Time">
              <Input value={form.eolIntervalTime} readOnly className="bg-gray-50" />
            </Field>

            <Field label="Maintainability Risk Level">
              <div className="py-1.5">
                <RiskLevelBadge level={form.maintainabilityRiskLevel} />
              </div>
            </Field>

            <Field label="Security Risk Level">
              <div className="py-1.5">
                <RiskLevelBadge level={form.securityRiskLevel} />
              </div>
            </Field>

            <Field label="CVSS V3 Score">
              <Input value={form.cvssV3Score ?? ''} readOnly className="bg-gray-50" />
            </Field>
          </div>
        </div>

        {errors._global && (
          <p className="px-6 text-sm text-red-600">{errors._global}</p>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" onClick={handleSave} loading={saving}>Save</Button>
        </div>
      </div>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs text-gray-600 mb-1">
        {required && <span className="text-red-500 mr-0.5">*</span>}
        {label}
      </label>
      {children}
      {error && <p className="mt-0.5 text-xs text-red-500">{error}</p>}
    </div>
  );
}
