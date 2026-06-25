'use client';

import { useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { Plus, Upload, Download, Mail, Eye, ArrowDownToLine, Pencil, Trash2, FileDown, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { Drawer, Form, Input, Select, DatePicker, Button, Modal, App, Steps, Table, Tooltip } from 'antd';
import { ResourceAutoComplete } from '@/shared/components/ui/ResourceAutoComplete';
import { authHeaders } from '@/shared/lib/auth-token';
import { appConfig } from '@/shared/lib/app-config';
import dayjs from 'dayjs';
import type { FormInstance, TableProps } from 'antd';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

/** IT Code field that auto-fills User Name when a resource is selected */
function ItCodeField({ value, onChange, form }: { value?: string; onChange?: (v: string) => void; form: FormInstance }) {
  return (
    <ResourceAutoComplete
      value={value}
      onChange={(val, resource) => {
        const itcode = resource?.itcode || val;
        onChange?.(itcode);
        if (resource?.name) {
          form.setFieldValue('ownerName', resource.name);
        }
      }}
      placeholder="Search by name or IT code"
    />
  );
}

const CERT_TYPE_OPTIONS = appConfig.certificationTypes;

const DURATION_OPTIONS = [
  { label: '12', value: 12 },
  { label: '24', value: 24 },
  { label: '36', value: 36 },
];

const searchFields: SearchField[] = [
  { key: 'certId', label: 'Certificate No.', type: 'text', placeholder: 'Certificate No.' },
  { key: 'name', label: 'Exam Name', type: 'text', placeholder: 'Exam Name' },
  { key: 'type', label: 'Certificate Type', type: 'select', options: CERT_TYPE_OPTIONS },
  { key: 'itCode', label: 'IT Code', type: 'text', placeholder: 'IT Code' },
  { key: 'status', label: 'Status', type: 'select', options: [
    { label: 'Valid', value: 'Valid' },
    { label: 'Expired', value: 'Expired' },
  ]},
];

export default function CertificationPage() {
  const { message, modal } = App.useApp();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any>(null);
  const [viewOnly, setViewOnly] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  // Import wizard state
  const [importOpen, setImportOpen] = useState(false);
  const [importStep, setImportStep] = useState(0);
  const [importLoading, setImportLoading] = useState(false);
  const [validateData, setValidateData] = useState<any[]>([]);
  const [importResults, setImportResults] = useState<any[]>([]);
  const [importSummary, setImportSummary] = useState<{ total: number; success: number; failed: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Row selection for export
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [exporting, setExporting] = useState(false);

  const isEdit = !!editingRecord;

  const { data, isLoading } = useQuery({
    queryKey: ['certifications', page, pageSize, filters],
    queryFn: () => api.get<any>('/certifications', { page, pageSize, ...filters }),
  });

  // ── Drawer handlers ──

  const openCreate = () => {
    setEditingRecord(null);
    setViewOnly(false);
    form.resetFields();
    setDrawerOpen(true);
  };

  const fillForm = (record: any) => {
    form.setFieldsValue({
      certId: record.certId,
      name: record.name,
      itCode: record.itCode,
      ownerName: record.ownerName,
      type: record.type,
      issuedDate: record.issuedDate ? dayjs(record.issuedDate) : null,
      duration: record.duration ? Number(record.duration) : undefined,
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : null,
      comment: record.comment,
    });
  };

  const openView = (record: any) => {
    setEditingRecord(record);
    setViewOnly(true);
    fillForm(record);
    setDrawerOpen(true);
  };

  const openEdit = (record: any) => {
    setEditingRecord(record);
    setViewOnly(false);
    fillForm(record);
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const payload: any = {
        name: values.name,
        itCode: values.itCode,
        ownerName: values.ownerName,
        type: values.type,
        issuedDate: values.issuedDate?.format('YYYY-MM-DD') || null,
        duration: values.duration,
        expiryDate: values.expiryDate?.format('YYYY-MM-DD') || null,
        comment: values.comment || null,
      };
      if (isEdit) {
        await api.put(`/certifications/${editingRecord.id}`, payload);
        message.success('Certification updated successfully');
      } else {
        await api.post('/certifications', payload);
        message.success('Certification created successfully');
      }
      setDrawerOpen(false);
      queryClient.invalidateQueries({ queryKey: ['certifications'] });
    } catch (err: any) {
      if (err?.errorFields) return;
      message.error(isEdit ? 'Failed to update' : 'Failed to create');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (record: any) => {
    modal.confirm({
      title: 'Delete Certification',
      content: `Are you sure you want to delete "${record.certId}"?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await api.delete(`/certifications/${record.id}`);
          message.success('Deleted successfully');
          queryClient.invalidateQueries({ queryKey: ['certifications'] });
          if (drawerOpen) setDrawerOpen(false);
        } catch {
          message.error('Failed to delete');
        }
      },
    });
  };

  // ── Certificate preview / download ──

  const handleView = async (record: any) => {
    const headers = authHeaders();
    const res = await fetch(`${API_BASE}/certifications/${record.id}/image`, { headers });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    setPreviewUrl(url);
    setPreviewOpen(true);
  };

  const handleDownload = async (record: any) => {
    const headers = authHeaders();
    const res = await fetch(`${API_BASE}/certifications/${record.id}/pdf`, { headers });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${record.certId || 'Certificate'}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  // Auto-compute Expiration Date = Issue Date + Duration
  const onIssueDateOrDurationChange = () => {
    const issuedDate = form.getFieldValue('issuedDate');
    const duration = form.getFieldValue('duration');
    if (issuedDate && duration) {
      form.setFieldValue('expiryDate', dayjs(issuedDate).add(duration, 'month'));
    }
  };

  // ── Import handlers ──

  const openImportModal = () => {
    setImportStep(0);
    setValidateData([]);
    setImportResults([]);
    setImportSummary(null);
    setSelectedFile(null);
    setImportOpen(true);
  };

  const handleDownloadTemplate = async () => {
    const headers = authHeaders();
    const res = await fetch(`${API_BASE}/certifications/template/download`, { headers });
    if (!res.ok) { message.error('Failed to download template'); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'certification_import_template.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleValidate = async () => {
    if (!selectedFile) { message.warning('Please select a file first'); return; }
    setImportLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const headers = authHeaders();
      const res = await fetch(`${API_BASE}/certifications/import/validate`, {
        method: 'POST', headers, body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        message.error(err.detail || 'Validation failed');
        return;
      }
      const result = await res.json();
      setValidateData(result.data || []);
      setImportStep(1);
    } catch { message.error('Failed to validate file'); }
    finally { setImportLoading(false); }
  };

  const handleConfirmImport = async () => {
    setImportLoading(true);
    try {
      const res = await fetch(`${API_BASE}/certifications/import/confirm`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ rows: validateData }),
      });
      if (!res.ok) { message.error('Import failed'); return; }
      const result = await res.json();
      setImportResults(result.data || []);
      setImportSummary({ total: result.total, success: result.success, failed: result.failed });
      setImportStep(2);
      queryClient.invalidateQueries({ queryKey: ['certifications'] });
      message.success(`Imported ${result.success} of ${result.total} records`);
    } catch { message.error('Import failed'); }
    finally { setImportLoading(false); }
  };

  const handleExportResultLog = () => {
    const dataToExport = importStep === 2 ? importResults : validateData;
    const rows = dataToExport.map((r: any) => [
      r.result, r.certId, r.examName, r.itCode, r.userName,
      r.certificateType, r.issueDate, r.expirationDate, r.warnings?.join('; ') || '',
    ].join(','));
    const csv = 'Result,Certificate No.,Exam Name,IT Code,User Name,Certificate Type,Issue Date,Expiration Date,Warnings\n' + rows.join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'import_result_log.csv';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  // ── Email handler ──

  const [emailing, setEmailing] = useState(false);

  const handleSendEmail = () => {
    modal.confirm({
      title: 'Send Expiration Notification',
      content: 'This will send an email to all EA team members listing certifications that are expired or expiring within 30 days. Continue?',
      okText: 'Send',
      onOk: async () => {
        setEmailing(true);
        try {
          const res = await fetch(`${API_BASE}/certifications/send-expiration-notification`, {
            method: 'POST',
            headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          });
          const result = await res.json();
          if (!res.ok) {
            message.error(result.detail || 'Failed to send notification');
            return;
          }
          if (result.count === 0) {
            message.info(result.message);
          } else {
            message.success(result.message);
          }
        } catch {
          message.error('Failed to send notification');
        } finally {
          setEmailing(false);
        }
      },
    });
  };

  // ── Export handler ──

  const handleExport = async () => {
    setExporting(true);
    try {
      const body: any = {};
      if (selectedRowKeys.length > 0) {
        body.ids = selectedRowKeys;
      } else {
        body.filters = filters;
      }
      const res = await fetch(`${API_BASE}/certifications/export`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) { message.error('Export failed'); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'certifications_export.xlsx';
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      message.success(selectedRowKeys.length > 0
        ? `Exported ${selectedRowKeys.length} selected records`
        : 'Exported all records');
    } catch { message.error('Export failed'); }
    finally { setExporting(false); }
  };

  // ── Import preview table columns ──

  const importColumns = [
    { title: 'Result', dataIndex: 'result', key: 'result', width: 140,
      render: (v: string, r: any) => {
        const isOk = v === 'OK' || v?.startsWith('Successfully');
        const isWarn = v === 'Warning';
        return (
          <Tooltip title={r.warnings?.join('\n')}>
            <span className={`flex items-center gap-1 text-xs ${isOk ? 'text-green-600' : isWarn ? 'text-orange-500' : 'text-red-500'}`}>
              {isOk ? <CheckCircle2 className="w-3.5 h-3.5" /> : isWarn ? <AlertTriangle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {v?.length > 18 ? v.slice(0, 18) + '...' : v}
            </span>
          </Tooltip>
        );
      },
    },
    { title: 'Certificate No.', dataIndex: 'certId', key: 'certId', width: 160, ellipsis: true },
    { title: 'Exam Name', dataIndex: 'examName', key: 'examName', width: 140, ellipsis: true },
    { title: 'IT Code', dataIndex: 'itCode', key: 'itCode', width: 100 },
    { title: 'User Name', dataIndex: 'userName', key: 'userName', width: 130, ellipsis: true },
    { title: 'Certificate Type', dataIndex: 'certificateType', key: 'certificateType', width: 140, ellipsis: true },
    { title: 'Issue Date', dataIndex: 'issueDate', key: 'issueDate', width: 110 },
    { title: 'Expiration Date', dataIndex: 'expirationDate', key: 'expirationDate', width: 130 },
  ];

  // ── Row selection config ──

  const rowSelection: TableProps<any>['rowSelection'] = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  };

  // ── Columns ──

  const columns: Column<any>[] = [
    { key: 'certId', title: 'Certificate No.', sortable: true, pinned: 'left', render: (v, record) => (
      <a className="text-primary-blue font-medium cursor-pointer hover:underline" onClick={() => openView(record)}>{v}</a>
    )},
    { key: 'name', title: 'Exam Name', sortable: true },
    { key: 'itCode', title: 'IT Code', sortable: true },
    { key: 'ownerName', title: 'User Name', sortable: true },
    { key: 'type', title: 'Certificate Type', sortable: true, width: '150' },
    { key: 'issuedDate', title: 'Issue Date', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString('en-CA') : '' },
    { key: 'duration', title: 'Duration(Months)', sortable: true },
    { key: 'expiryDate', title: 'Expiration Date', sortable: true, render: (v) => v ? new Date(v).toLocaleDateString('en-CA') : '' },
    { key: 'status', title: 'Status', sortable: true, render: (v) => (
      <span className={v === 'Valid' ? 'text-green-600' : v === 'Expired' ? 'text-red-500' : ''}>{v}</span>
    )},
    { key: 'operation', title: 'Operation', width: '150', pinned: 'right', render: (_v, record) => (
      <div className="flex items-center gap-3">
        <button onClick={(e) => { e.stopPropagation(); handleView(record); }} className="text-[#909399] hover:text-primary-blue" title="Preview">
          <Eye className="w-4 h-4" />
        </button>
        <button onClick={(e) => { e.stopPropagation(); handleDownload(record); }} className="text-[#909399] hover:text-primary-blue" title="Download">
          <ArrowDownToLine className="w-4 h-4" />
        </button>
        <button onClick={(e) => { e.stopPropagation(); openEdit(record); }} className="text-[#909399] hover:text-primary-blue" title="Edit">
          <Pencil className="w-4 h-4" />
        </button>
        <button onClick={(e) => { e.stopPropagation(); handleDelete(record); }} className="text-[#909399] hover:text-red-500" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    )},
  ];

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">Certification</h1>

      <SearchForm
        fields={searchFields}
        onSearch={(v) => { setFilters(v); setPage(1); }}
        onReset={() => { setFilters({}); setPage(1); }}
      />

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-3">
        <button onClick={openCreate} className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary-blue border border-primary-blue rounded hover:bg-blue-50">
          <Plus className="w-3.5 h-3.5" />
          New
        </button>
        <button onClick={openImportModal} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary">
          <Upload className="w-3.5 h-3.5" />
          Import
        </button>
        <button onClick={handleExport} disabled={exporting} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary disabled:opacity-50">
          <Download className="w-3.5 h-3.5" />
          {exporting ? 'Exporting...' : selectedRowKeys.length > 0 ? `Export (${selectedRowKeys.length})` : 'Export'}
        </button>
        <button onClick={handleSendEmail} disabled={emailing} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary disabled:opacity-50">
          <Mail className="w-3.5 h-3.5" />
          {emailing ? 'Sending...' : 'Email'}
        </button>
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="id"
        loading={isLoading}
        showColumnSettings
        rowSelection={rowSelection}
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

      {/* Certificate Preview Modal */}
      <Modal
        open={previewOpen}
        title="Certificate Preview"
        footer={null}
        onCancel={() => { setPreviewOpen(false); URL.revokeObjectURL(previewUrl); }}
        width={720}
        destroyOnHidden
      >
        {previewUrl && (
          <img src={previewUrl} alt="Certificate" style={{ width: '100%' }} />
        )}
      </Modal>

      {/* Create / Edit Drawer */}
      <Drawer
        title="Certification"
        placement="right"
        styles={{ wrapper: { width: 1100 } }}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnHidden
        footer={
          <div className="flex justify-between">
            <div className="flex gap-2">
              {viewOnly ? (
                <Button type="primary" onClick={() => setViewOnly(false)}>Edit</Button>
              ) : isEdit ? (
                <>
                  <Button onClick={handleSave} type="primary" loading={saving}>Save</Button>
                  <Button danger onClick={() => handleDelete(editingRecord)}>Delete</Button>
                </>
              ) : (
                <Button onClick={handleSave} type="primary" loading={saving}>Save</Button>
              )}
            </div>
            <div className="flex gap-2">
              {isEdit && (
                <>
                  <Button onClick={() => handleView(editingRecord)} icon={<Eye className="w-3.5 h-3.5" />}>Preview</Button>
                  <Button onClick={() => handleDownload(editingRecord)} icon={<ArrowDownToLine className="w-3.5 h-3.5" />}>Download</Button>
                </>
              )}
              <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            </div>
          </div>
        }
      >
        <div className="text-sm font-medium text-text-primary mb-4">General Data</div>
        <Form form={form} layout="vertical">

          {isEdit && (
            <Form.Item label="Certificate No." name="certId">
              <Input disabled />
            </Form.Item>
          )}

          <Form.Item label="Exam Name" name="name" rules={[{ required: !viewOnly, message: 'Please enter exam name' }]}>
            <Input placeholder="Enter exam name" disabled={viewOnly} />
          </Form.Item>

          <Form.Item label="IT Code" name="itCode" rules={[{ required: !viewOnly, message: 'Please select IT Code' }]}>
            {viewOnly ? <Input disabled /> : <ItCodeField form={form} />}
          </Form.Item>

          <Form.Item label="User Name" name="ownerName" rules={[{ required: !viewOnly, message: 'Please enter user name' }]}>
            <Input disabled placeholder="Auto-filled from IT Code" />
          </Form.Item>

          <Form.Item label="Certificate Type" name="type" rules={[{ required: !viewOnly, message: 'Please select certificate type' }]}>
            <Select options={CERT_TYPE_OPTIONS} placeholder="Select certificate type" disabled={viewOnly} />
          </Form.Item>

          {!viewOnly && <div className="text-red-500 text-xs mb-3">Required</div>}

          <div className="grid grid-cols-4 gap-3">
            <Form.Item label="Issue Date" name="issuedDate" className="col-span-1">
              <DatePicker className="w-full" onChange={() => onIssueDateOrDurationChange()} disabled={viewOnly} />
            </Form.Item>
            <Form.Item label="Duration(Months)" name="duration" className="col-span-1">
              <Select options={DURATION_OPTIONS} placeholder="Select" onChange={() => setTimeout(onIssueDateOrDurationChange, 0)} disabled={viewOnly} />
            </Form.Item>
            <Form.Item label="Expiration Date" name="expiryDate" className="col-span-1">
              <DatePicker className="w-full" disabled={viewOnly} />
            </Form.Item>
            <Form.Item label="Status" className="col-span-1">
              <Input disabled value={isEdit ? (editingRecord?.status || '') : ''} />
            </Form.Item>
          </div>

          <Form.Item label="Comment" name="comment">
            <Input.TextArea rows={4} placeholder="Enter comment" disabled={viewOnly} />
          </Form.Item>
        </Form>
      </Drawer>

      {/* Import Wizard Modal */}
      <Modal
        open={importOpen}
        title={null}
        footer={null}
        onCancel={() => setImportOpen(false)}
        width={960}
        destroyOnHidden
      >
        <Steps
          current={importStep}
          className="mb-6 mt-2"
          items={[
            { title: 'Select a file' },
            { title: 'Validate the data', description: 'Alert message' },
            { title: 'Import Result' },
          ]}
        />

        {importStep === 0 && (
          <div>
            <a onClick={handleDownloadTemplate} className="flex items-center gap-2 text-primary-blue cursor-pointer mb-4 font-medium">
              <FileDown className="w-4 h-4" /> Download Template
            </a>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <div className="flex justify-center mb-3">
                <Upload className="w-12 h-12 text-blue-400" />
              </div>
              <input ref={fileInputRef} type="file" accept=".xls,.xlsx" onChange={handleFileSelect} className="hidden" />
              <Button onClick={() => fileInputRef.current?.click()}>
                {selectedFile ? selectedFile.name : 'Upload file'}
              </Button>
              <p className="text-gray-400 text-sm mt-2">Please upload the file, Only the .xls/.xlsx format is supported.</p>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              <div className="font-medium text-gray-700 mb-1">Instructions:</div>
              <ol className="list-decimal ml-5 space-y-0.5">
                <li>Download the data template fill in the data according to the data rules/comments in the template.</li>
                <li>Or we can use the search function to export some data into an Excel file. Change the data and upload the change data.</li>
                <li>Then select and upload the file. The system would validate and import the data.</li>
                <li>We can export the data validation results for all the errors/warnings.</li>
                <li>Max <strong>5000</strong> records are supported.</li>
              </ol>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <Button onClick={() => setImportOpen(false)}>Cancel</Button>
              <Button type="primary" onClick={handleValidate} loading={importLoading} disabled={!selectedFile}>
                Validate the data
              </Button>
            </div>
          </div>
        )}

        {importStep === 1 && (
          <div>
            <Table
              columns={importColumns}
              dataSource={validateData}
              rowKey={(_, i) => String(i)}
              size="small"
              scroll={{ x: 'max-content', y: 400 }}
              pagination={{ pageSize: 10, showTotal: (t) => `Total ${t} Items`, size: 'small' }}
            />
            <div className="flex justify-between items-center mt-4">
              <Button onClick={handleExportResultLog} icon={<Download className="w-3.5 h-3.5" />}>Result Log</Button>
              <div className="flex gap-2">
                <Button onClick={() => setImportOpen(false)}>Cancel</Button>
                <Button onClick={() => setImportStep(0)}>Previous</Button>
                <Button type="primary" onClick={handleConfirmImport} loading={importLoading}>Confirm to Import</Button>
              </div>
            </div>
          </div>
        )}

        {importStep === 2 && (
          <div>
            <div className="font-medium text-gray-700 mb-3">
              Import Completed
              {importSummary && (
                <span className="text-sm font-normal text-gray-500 ml-2">
                  (Success: {importSummary.success}, Failed: {importSummary.failed})
                </span>
              )}
            </div>
            <Table
              columns={importColumns}
              dataSource={importResults}
              rowKey={(_, i) => String(i)}
              size="small"
              scroll={{ x: 'max-content', y: 400 }}
              pagination={{ pageSize: 10, showTotal: (t) => `Total ${t} Items`, size: 'small' }}
            />
            <div className="flex justify-between items-center mt-4">
              <Button onClick={handleExportResultLog} icon={<Download className="w-3.5 h-3.5" />}>Result Log</Button>
              <Button type="primary" onClick={() => setImportOpen(false)}>View Details</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
