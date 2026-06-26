'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { DatePicker, Input, Select, message } from 'antd';
import dayjs from 'dayjs';
import { api } from '@/shared/lib/api';

const { TextArea } = Input;

type ResourceOption = {
  key: string;
  value: string;
  itcode: string;
  name: string;
};

type ProjectCreatePayload = {
  projectName: string;
  type?: string | null;
  startDate?: string | null;
  goLiveDate?: string | null;
  duration?: number | null;
  objectives?: string | null;
  status?: string | null;
  category?: string | null;
  aiRelated?: string | null;
  pm?: string | null;
  pmItcode?: string | null;
  dtLead?: string | null;
  dtLeadItcode?: string | null;
  itLead?: string | null;
  itLeadItcode?: string | null;
  comment?: string | null;
};

type ResourceState = {
  keyword: string;
  value: string | undefined;
  label: string;
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white border border-border-light rounded-lg p-4 md:p-5">
      <h2 className="text-base font-semibold text-text-primary mb-4">{title}</h2>
      {children}
    </section>
  );
}

function Label({ text, required }: { text: string; required?: boolean }) {
  return (
    <label className="text-sm text-text-primary whitespace-nowrap flex items-center justify-end md:justify-end">
      {required && <span className="text-red-500 mr-1">*</span>}
      {text}
    </label>
  );
}

export default function CreateProjectPage() {
  const router = useRouter();
  const [messageApi, contextHolder] = message.useMessage();

  const [form, setForm] = useState({
    projectName: '',
    type: undefined as string | undefined,
    objectives: '',
    status: 'In Progress',
    category: 'regular',
    startDate: null as string | null,
    goLiveDate: null as string | null,
    duration: '' as string,
    aiRelated: undefined as string | undefined,
    comment: '',
  });

  const [pm, setPm] = useState<ResourceState>({ keyword: '', value: undefined, label: '' });
  const [dtLead, setDtLead] = useState<ResourceState>({ keyword: '', value: undefined, label: '' });
  const [itLead, setItLead] = useState<ResourceState>({ keyword: '', value: undefined, label: '' });

  const { data: pmOptions = [], isFetching: pmLoading } = useQuery<ResourceOption[]>({
    queryKey: ['project-create-resource-pm', pm.keyword],
    queryFn: () => api.get<ResourceOption[]>('/resources/search', { q: pm.keyword, limit: 20 }),
    enabled: true,
    staleTime: 30_000,
  });

  const { data: dtOptions = [], isFetching: dtLoading } = useQuery<ResourceOption[]>({
    queryKey: ['project-create-resource-dt', dtLead.keyword],
    queryFn: () => api.get<ResourceOption[]>('/resources/search', { q: dtLead.keyword, limit: 20 }),
    enabled: true,
    staleTime: 30_000,
  });

  const { data: itOptions = [], isFetching: itLoading } = useQuery<ResourceOption[]>({
    queryKey: ['project-create-resource-it', itLead.keyword],
    queryFn: () => api.get<ResourceOption[]>('/resources/search', { q: itLead.keyword, limit: 20 }),
    enabled: true,
    staleTime: 30_000,
  });

  const categoryOptions = [
    { label: 'PMO Regular', value: 'regular' },
    { label: 'Operational', value: 'operational' },
  ];

  const requestTypeOptions = [
    { label: 'Project', value: 'Project' },
    { label: 'Enhancement', value: 'Enhancement' },
    { label: 'Maintenance', value: 'Maintenance' },
  ];

  const statusOptions = [
    { label: 'In Progress', value: 'In Progress' },
    { label: 'Draft', value: 'Draft' },
    { label: 'Completed', value: 'Completed' },
  ];

  const aiRelatedOptions = [
    { label: 'Yes', value: 'Yes' },
    { label: 'No', value: 'No' },
  ];

  const toSelectOptions = (list: ResourceOption[]) =>
    list.map((r) => ({
      label: `${r.itcode}-${r.name}`,
      value: r.itcode,
      meta: r,
    }));

  const pmSelectOptions = useMemo(() => toSelectOptions(pmOptions), [pmOptions]);
  const dtSelectOptions = useMemo(() => toSelectOptions(dtOptions), [dtOptions]);
  const itSelectOptions = useMemo(() => toSelectOptions(itOptions), [itOptions]);

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload: ProjectCreatePayload = {
        projectName: form.projectName.trim(),
        type: form.type || null,
        objectives: form.objectives.trim() || null,
        status: form.status || null,
        category: form.category,
        startDate: form.startDate,
        goLiveDate: form.goLiveDate,
        duration: form.duration ? Number(form.duration) : null,
        aiRelated: form.aiRelated || null,
        pm: pm.label || null,
        pmItcode: pm.value || null,
        dtLead: dtLead.label || null,
        dtLeadItcode: dtLead.value || null,
        itLead: itLead.label || null,
        itLeadItcode: itLead.value || null,
        comment: form.comment.trim() || null,
      };
      return api.post<any>('/projects', payload);
    },
    onSuccess: (data) => {
      messageApi.success('Project created');
      const pid = data?.projectId;
      if (pid) {
        router.push(`/projects/${encodeURIComponent(pid)}`);
      } else {
        router.push('/projects');
      }
    },
    onError: () => {
      messageApi.error('Failed to create project');
    },
  });

  const validate = (): boolean => {
    if (!form.projectName.trim()) {
      messageApi.error('Project Name is required');
      return false;
    }
    if (!form.startDate) {
      messageApi.error('Start Date is required');
      return false;
    }
    if (!form.goLiveDate) {
      messageApi.error('Go Live Date is required');
      return false;
    }
    if (form.startDate && form.goLiveDate && !dayjs(form.goLiveDate).isAfter(dayjs(form.startDate), 'day')) {
      messageApi.error('Go Live Date must be later than Start Date');
      return false;
    }
    if (!pm.value) {
      messageApi.error('PM is required');
      return false;
    }
    return true;
  };

  const handleSave = () => {
    if (!validate()) return;
    createMutation.mutate();
  };

  const handleResourceSelect = (
    value: string,
    options: ResourceOption[],
    setter: (state: ResourceState) => void,
  ) => {
    const selected = options.find((o) => o.itcode === value);
    setter({
      keyword: selected ? `${selected.itcode}-${selected.name}` : value,
      value: selected?.itcode,
      label: selected?.name || '',
    });
  };

  return (
    <div className="p-6 space-y-4">
      {contextHolder}

      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-blue transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h1 className="text-lg font-semibold text-text-primary">Create a new project</h1>
      </div>

      <Section title="General Data">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-3">
          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Project ID" />
            <Input value="Automatically generate" disabled />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Status" />
            <Select
              value={form.status}
              options={statusOptions}
              onChange={(v) => setForm((p) => ({ ...p, status: v }))}
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Category" />
            <Select value={form.category} options={categoryOptions} onChange={(v) => setForm((p) => ({ ...p, category: v }))} />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Project Name" required />
            <Input
              value={form.projectName}
              onChange={(e) => setForm((p) => ({ ...p, projectName: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Start Date" required />
            <DatePicker
              value={form.startDate ? dayjs(form.startDate) : null}
              onChange={(d) => setForm((p) => ({ ...p, startDate: d ? d.format('YYYY-MM-DD') : null }))}
              disabledDate={(current) => {
                if (!form.goLiveDate) return false;
                return current.isSame(dayjs(form.goLiveDate), 'day') || current.isAfter(dayjs(form.goLiveDate), 'day');
              }}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Request Type" />
            <Select
              value={form.type}
              options={requestTypeOptions}
              onChange={(v) => setForm((p) => ({ ...p, type: v }))}
              allowClear
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Go Live Date" required />
            <DatePicker
              value={form.goLiveDate ? dayjs(form.goLiveDate) : null}
              onChange={(d) => setForm((p) => ({ ...p, goLiveDate: d ? d.format('YYYY-MM-DD') : null }))}
              disabledDate={(current) => {
                if (!form.startDate) return false;
                return current.isSame(dayjs(form.startDate), 'day') || current.isBefore(dayjs(form.startDate), 'day');
              }}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-start gap-3 md:row-span-2">
            <Label text="Objectives" />
            <TextArea
              rows={4}
              value={form.objectives}
              onChange={(e) => setForm((p) => ({ ...p, objectives: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Duration (Months)" />
            <Input
              value={form.duration}
              onChange={(e) => setForm((p) => ({ ...p, duration: e.target.value.replace(/[^0-9]/g, '') }))}
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="AI Related" />
            <Select
              value={form.aiRelated}
              options={aiRelatedOptions}
              onChange={(v) => setForm((p) => ({ ...p, aiRelated: v }))}
              allowClear
            />
          </div>
        </div>
      </Section>

      <Section title="Persons Responsible">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-3">
          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="PM" required />
            <Select
              showSearch
              value={pm.value || undefined}
              options={pmSelectOptions}
              onSearch={(kw) => setPm((prev) => ({ ...prev, keyword: kw }))}
              onSelect={(value) => handleResourceSelect(value, pmOptions, setPm)}
              onClear={() => setPm({ keyword: '', value: undefined, label: '' })}
              filterOption={false}
              loading={pmLoading}
              allowClear
              placeholder="Please enter"
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="IT Lead" />
            <Select
              showSearch
              value={itLead.value || undefined}
              options={itSelectOptions}
              onSearch={(kw) => setItLead((prev) => ({ ...prev, keyword: kw }))}
              onSelect={(value) => handleResourceSelect(value, itOptions, setItLead)}
              onClear={() => setItLead({ keyword: '', value: undefined, label: '' })}
              filterOption={false}
              loading={itLoading}
              allowClear
              placeholder="Please enter"
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-center gap-3">
            <Label text="Biz Analyst" />
            <Select
              showSearch
              value={dtLead.value || undefined}
              options={dtSelectOptions}
              onSearch={(kw) => setDtLead((prev) => ({ ...prev, keyword: kw }))}
              onSelect={(value) => handleResourceSelect(value, dtOptions, setDtLead)}
              onClear={() => setDtLead({ keyword: '', value: undefined, label: '' })}
              filterOption={false}
              loading={dtLoading}
              allowClear
              placeholder="Please enter"
            />
          </div>

          <div className="grid grid-cols-[180px_1fr] items-start gap-3 md:col-span-2">
            <Label text="Comments" />
            <TextArea
              rows={4}
              value={form.comment}
              onChange={(e) => setForm((p) => ({ ...p, comment: e.target.value }))}
            />
          </div>
        </div>
      </Section>

      <div className="flex justify-end gap-3">
        <button
          onClick={() => router.back()}
          className="px-6 py-2 border border-border-default rounded text-text-secondary hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={createMutation.isPending}
          className="px-6 py-2 rounded bg-primary-blue text-white hover:bg-primary-blue-hover disabled:opacity-60"
        >
          Save
        </button>
      </div>
    </div>
  );
}
