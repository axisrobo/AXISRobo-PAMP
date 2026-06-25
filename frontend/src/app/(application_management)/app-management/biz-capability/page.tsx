'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { authFetch, buildQueryString } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { ActionBar } from '@/shared/components/ui/ActionBar';
import { App, Button, Input, Modal, Table, Upload } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { useAuth } from '@/shared/lib/auth-context';

type BizCapabilityFilterKey = 'version' | 'domainL1' | 'subDomainL2' | 'capabilityGroupL3' | 'level';

type BizCapabilityFilters = {
  version: string;
  domainL1: string;
  subDomainL2: string;
  capabilityGroupL3: string;
  level: string;
};

type BizCapabilityFilterOptions = {
  domainL1?: string[];
  subDomainL2?: string[];
  capabilityGroupL3?: string[];
};

const EMPTY_BIZ_CAPABILITY_FILTERS: BizCapabilityFilters = {
  version: '',
  domainL1: '',
  subDomainL2: '',
  capabilityGroupL3: '',
  level: '',
};

function normalizeBizCapabilityFilters(values?: Partial<Record<string, string>>): BizCapabilityFilters {
  return {
    version: values?.version ?? '',
    domainL1: values?.domainL1 ?? '',
    subDomainL2: values?.subDomainL2 ?? '',
    capabilityGroupL3: values?.capabilityGroupL3 ?? '',
    level: values?.level ?? '',
  };
}

function applyCascadingChange(filters: BizCapabilityFilters, key: BizCapabilityFilterKey, rawValue: string): BizCapabilityFilters {
  const value = rawValue ?? '';
  if (key === 'version') {
    return {
      ...filters,
      version: value,
      domainL1: '',
      subDomainL2: '',
      capabilityGroupL3: '',
    };
  }
  if (key === 'domainL1') {
    return {
      ...filters,
      domainL1: value,
      subDomainL2: '',
      capabilityGroupL3: '',
    };
  }
  if (key === 'subDomainL2') {
    return {
      ...filters,
      subDomainL2: value,
      capabilityGroupL3: '',
    };
  }
  return {
    ...filters,
    [key]: value,
  };
}

function createInitialFilters(versions?: string[]): BizCapabilityFilters {
  return {
    ...EMPTY_BIZ_CAPABILITY_FILTERS,
    version: versions?.[0] ?? '',
  };
}

function invalidateWithOptions(filters: BizCapabilityFilters, options?: BizCapabilityFilterOptions): BizCapabilityFilters {
  if (!options) {
    return filters;
  }

  let next = filters;
  const l1Options = options.domainL1 ?? [];
  const l2Options = options.subDomainL2 ?? [];
  const l3Options = options.capabilityGroupL3 ?? [];

  if (next.domainL1 && !l1Options.includes(next.domainL1)) {
    next = {
      ...next,
      domainL1: '',
      subDomainL2: '',
      capabilityGroupL3: '',
    };
  }

  if (next.subDomainL2 && !l2Options.includes(next.subDomainL2)) {
    next = {
      ...next,
      subDomainL2: '',
      capabilityGroupL3: '',
    };
  }

  if (next.capabilityGroupL3 && !l3Options.includes(next.capabilityGroupL3)) {
    next = {
      ...next,
      capabilityGroupL3: '',
    };
  }

  return next;
}

function filtersEqual(left: BizCapabilityFilters, right: BizCapabilityFilters): boolean {
  return left.version === right.version
    && left.domainL1 === right.domainL1
    && left.subDomainL2 === right.subDomainL2
    && left.capabilityGroupL3 === right.capabilityGroupL3
    && left.level === right.level;
}

const searchFields: SearchField[] = [
  { key: 'version', label: 'Version', type: 'text', placeholder: 'Version' },
  { key: 'domainL1', label: 'Domain(L1)', type: 'select', placeholder: 'Domain(L1)', options: [] },
  { key: 'subDomainL2', label: 'Sub Domain(L2)', type: 'select', placeholder: 'Sub Domain(L2)', options: [] },
  { key: 'capabilityGroupL3', label: 'Capability Group(L3)', type: 'select', placeholder: 'Capability Group(L3)', options: [] },
  { key: 'level', label: 'Level', type: 'multiselect', options: [
    { label: 'L1', value: '1' },
    { label: 'L2', value: '2' },
    { label: 'L3', value: '3' },
    { label: 'L4', value: '4' },
  ]},
];

export default function BizCapabilityMasterDataPage() {
  const queryClient = useQueryClient();
  const { message } = App.useApp();
  const { hasRole } = useAuth();
  const isAdmin = hasRole('ea_admin');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<BizCapabilityFilters>(EMPTY_BIZ_CAPABILITY_FILTERS);
  const [importOpen, setImportOpen] = useState(false);
  const [importVersion, setImportVersion] = useState('');
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importFileList, setImportFileList] = useState<UploadFile[]>([]);
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [errorRows, setErrorRows] = useState<{ rowNo: string; errorResult: string }[]>([]);

  const { data: versionsData } = useQuery({
    queryKey: ['biz-capability-versions'],
    queryFn: () => api.get<{ versions: string[] }>('/biz-capability-master-data/versions'),
  });

  useEffect(() => {
    if (!versionsData?.versions?.length) {
      return;
    }
    setFilters((prev) => {
      if (prev.version) {
        return prev;
      }
      return {
        ...prev,
        version: versionsData.versions[0],
      };
    });
  }, [versionsData]);

  const { data: filterOptions } = useQuery({
    queryKey: ['biz-capability-filter-options', filters.version, filters.domainL1, filters.subDomainL2],
    queryFn: () => api.get<BizCapabilityFilterOptions>('/biz-capability-master-data/filter-options', {
      version: filters.version, 
      domainL1: filters.domainL1, 
      subDomainL2: filters.subDomainL2 
    }),
  });

  useEffect(() => {
    if (!filterOptions) {
      return;
    }
    setFilters((prev) => {
      const next = invalidateWithOptions(prev, filterOptions);
      return filtersEqual(prev, next) ? prev : next;
    });
  }, [filterOptions]);

  const dynamicSearchFields = useMemo(() => {
    const fields = searchFields.map(f => ({ ...f }));
    
    // Version dropdown
    if (versionsData?.versions) {
      const versionField = fields.find(f => f.key === 'version');
      if (versionField) {
        versionField.type = 'select';
        versionField.options = versionsData.versions.map(v => ({ label: v, value: v }));
      }
    }

    // Cascaded filter options
    if (filterOptions) {
      const l1Field = fields.find(f => f.key === 'domainL1');
      if (l1Field) l1Field.options = filterOptions.domainL1?.map((v: string) => ({ label: v, value: v })) || [];

      const l2Field = fields.find(f => f.key === 'subDomainL2');
      if (l2Field) l2Field.options = filterOptions.subDomainL2?.map((v: string) => ({ label: v, value: v })) || [];

      const l3Field = fields.find(f => f.key === 'capabilityGroupL3');
      if (l3Field) l3Field.options = filterOptions.capabilityGroupL3?.map((v: string) => ({ label: v, value: v })) || [];
    }
    
    return fields;
  }, [versionsData, filterOptions]);

  const { data, isLoading } = useQuery({
    queryKey: ['biz-capability', page, pageSize, filters],
    queryFn: () => api.get<any>('/biz-capability-master-data', { page, pageSize, ...filters }),
  });

  const columns: Column<any>[] = [
    { key: 'bcId', title: 'BC ID', sortable: true, render: (v) => <span className="text-primary-blue font-medium">{v}</span> },
    { key: 'parentBcId', title: 'Parent BC ID', sortable: true },
    { key: 'bcName', title: 'BC Name', sortable: true },
    { key: 'bcNameCn', title: 'BC Name (CN)' },
    { key: 'domainL1', title: 'Domain L1', sortable: true },
    { key: 'subDomainL2', title: 'Sub Domain L2', sortable: true },
    { key: 'capabilityGroupL3', title: 'Capability Group L3', sortable: true },
    { key: 'level', title: 'Level', sortable: true },
    { key: 'bcDescription', title: 'Description' },
    { key: 'alias', title: 'Alias' },
    { key: 'bizGroup', title: 'Biz Group' },
    { key: 'geo', title: 'Geo' },
    { key: 'bizOwner', title: 'Biz Owner' },
    { key: 'bizTeam', title: 'Biz Team' },
    { key: 'dtOwner', title: 'DT Owner' },
    { key: 'dtTeam', title: 'DT Team' },
    { key: 'remark', title: 'Remark' },
    { key: 'version', title: 'Version', sortable: true },
  ];

  const importErrorColumns: ColumnsType<{ rowNo: string; errorResult: string }> = useMemo(
    () => [
      { title: 'Row no.', dataIndex: 'rowNo', key: 'rowNo', width: 120 },
      { title: 'Error Result', dataIndex: 'errorResult', key: 'errorResult' },
    ],
    []
  );

  const resetImportState = () => {
    setImportOpen(false);
    setImportVersion('');
    setImportFile(null);
    setImportFileList([]);
    setErrorRows([]);
  };

  const validateImport = async (file: File, dataVersion: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataVersion', dataVersion);
    setValidating(true);
    try {
      const res = await api.postForm<{ valid: boolean; errorRows: { rowNo: string; errorResult: string }[] }>(
        '/biz-capability-master-data/import/validate',
        formData
      );
      setErrorRows(res.errorRows || []);
      return res.valid;
    } catch (e: any) {
      setErrorRows([{ rowNo: '-', errorResult: e?.message || 'Validation failed' }]);
      return false;
    } finally {
      setValidating(false);
    }
  };

  useEffect(() => {
    if (!importFile) return;
    if (!importVersion.trim()) {
      setErrorRows([{ rowNo: '-', errorResult: 'Please input Data Version to run pre-validation' }]);
      return;
    }
    validateImport(importFile, importVersion.trim());
  }, [importFile, importVersion]);

  const handleConfirmImport = async () => {
    if (!importVersion.trim()) {
      message.error('Data Version is required');
      return;
    }
    if (!importFile) {
      message.error('Please upload an Excel file');
      return;
    }

    const valid = await validateImport(importFile, importVersion.trim());
    if (!valid) {
      message.error('Data completeness check failed. Please fix the file and retry.');
      return;
    }

    const formData = new FormData();
    formData.append('file', importFile);
    formData.append('dataVersion', importVersion.trim());

    setImporting(true);
    try {
      const res = await api.postForm<{ success: boolean; imported: number; errorRows: { rowNo: string; errorResult: string }[] }>(
        '/biz-capability-master-data/import',
        formData
      );
      if (!res.success) {
        setErrorRows(res.errorRows || []);
        message.error('Import failed. Please review errors.');
        return;
      }
      message.success(`Imported ${res.imported} row(s)`);
      await queryClient.invalidateQueries({ queryKey: ['biz-capability'] });
      await queryClient.invalidateQueries({ queryKey: ['biz-capability-versions'] });
      await queryClient.invalidateQueries({ queryKey: ['biz-capability-filter-options'] });
      resetImportState();
    } catch (e: any) {
      message.error(e?.message || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async () => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
    const query = buildQueryString(filters);
    const res = await authFetch(`${API_BASE}/biz-capability-master-data/export${query}`);
    if (!res.ok) {
      throw new Error(`Export failed: ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `biz-capability-master-data-${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Business Capability Master Data</h1>

      <SearchForm
        fields={dynamicSearchFields}
        initialValues={filters}
        resetToInitialValues
        onSearch={(v) => { setFilters(normalizeBizCapabilityFilters(v)); setPage(1); }}
        onReset={() => { setFilters(createInitialFilters(versionsData?.versions)); setPage(1); }}
        onChange={(key, value) => {
          if (!['version', 'domainL1', 'subDomainL2', 'capabilityGroupL3', 'level'].includes(key)) {
            return;
          }
          const typedKey = key as BizCapabilityFilterKey;
          const nextValue = Array.isArray(value) ? value.join(',') : value;
          setFilters((prev) => applyCascadingChange(prev, typedKey, nextValue));
          setPage(1);
        }}
      />

      <ActionBar
        showImport={isAdmin}
        showExport
        onImport={() => setImportOpen(true)}
        onExport={async () => {
          try {
            await handleExport();
            message.success('Export started');
          } catch (e: any) {
            message.error(e?.message || 'Export failed');
          }
        }}
      />

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="id"
        loading={isLoading}
        showColumnSettings
      />
      {data && (
        <Pagination
          currentPage={page}
          totalPages={data.totalPages || 1}
          totalItems={data.total || 0}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        />
      )}

      <Modal
        title="Import Business Capability Master Data"
        open={importOpen}
        onCancel={resetImportState}
        footer={[
          <Button key="cancel" onClick={resetImportState}>
            Cancel
          </Button>,
          <Button key="confirm" type="primary" loading={importing || validating} onClick={handleConfirmImport}>
            Confirm Import
          </Button>,
        ]}
        width={760}
        destroyOnHidden
      >
        <div className="mb-3 flex items-center gap-3">
          <label className="w-28 text-base text-text-primary">
            <span className="text-red-500">* </span>
            Data Version:
          </label>
          <Input
            value={importVersion}
            onChange={(e) => setImportVersion(e.target.value)}
            placeholder="Input Data Version"
            className="flex-1"
          />
        </div>

        <Upload.Dragger
          accept=".xlsx,.xls,.xlsm"
          multiple={false}
          fileList={importFileList}
          beforeUpload={(file) => {
            setImportFile(file as File);
            setImportFileList([file]);
            return false;
          }}
          onRemove={() => {
            setImportFile(null);
            setImportFileList([]);
            setErrorRows([]);
          }}
          className="mb-4"
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Drag a file here, or click to upload</p>
        </Upload.Dragger>

        <div className="mb-2 text-base font-medium">Error Result</div>
        <Table
          size="small"
          bordered
          pagination={false}
          rowKey={(r) => `${r.rowNo}-${r.errorResult}`}
          columns={importErrorColumns}
          dataSource={errorRows}
          locale={{ emptyText: 'No errors' }}
        />
      </Modal>
    </div>
  );
}
