'use client';

import { useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { DataTable, Column } from '@/shared/components/ui/DataTable';
import { Pagination } from '@/shared/components/ui/Pagination';
import { SearchForm, SearchField } from '@/shared/components/ui/SearchForm';
import { ConfirmDialog } from '@/shared/components/ui/ConfirmDialog';
import { ExportButton } from '@/shared/components/ui/ExportButton';
import { Plus, Upload, Pencil, Trash2, CloudUpload, X, FileText, Download } from 'lucide-react';
import { useAuth } from '@/shared/lib/auth-context';
import { Modal } from 'antd';
import {
  EA_ADVICE_OPTIONS,
  MasterRecord,
} from '@/features/tech-stack/components/master-data/MasterDataForm';
import { MasterDataDrawer } from '@/features/tech-stack/components/master-data/MasterDataDrawer';

// ── CSV Template Download ──────────────────────────────────────

const CSV_TEMPLATE_HEADERS = [
  'Category', 'Source Type', 'Source', 'Sub Category', 'Technology Component', 'Component Package Name',
  'Version', 'Major Version', 'Minor Version', 'Patch Version',
  'EA Advice', 'Standard', 'Restricted', 'Remark',
  'EOL Date', 'Security Vulnerability', 'Security Severity', 'CVSS V3 Score',
];

function downloadTemplate() {
  const bom = '\uFEFF';
  const csv = bom + CSV_TEMPLATE_HEADERS.join(',') + '\r\n';
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'technology-stack-import-template.csv';
  a.click();
  URL.revokeObjectURL(url);
}

// ── Import Modal ───────────────────────────────────────────────

interface ImportResult {
  success: number;
  failed: number;
  errors: string[];
}

interface ImportModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

function ImportModal({ open, onClose, onSuccess }: ImportModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const reset = () => { setFile(null); setResult(null); setImporting(false); };

  const handleClose = () => { reset(); onClose(); };

  const ACCEPTED_EXTS = ['.csv', '.xls', '.xlsx', '.doc', '.docx', '.pdf'];
  const isAccepted = (f: File) => ACCEPTED_EXTS.some(ext => f.name.toLowerCase().endsWith(ext));

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && isAccepted(f)) setFile(f);
  };

  const handleConfirm = async () => {
    if (!file) return;
    setImporting(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await api.postForm<ImportResult>('/technology-stack/import', fd);
      setResult(res);
      if (res.failed === 0) {
        onSuccess();
        handleClose();
      }
    } catch {
      setResult({ success: 0, failed: 1, errors: ['Failed to upload. Please check the file format.'] });
    } finally {
      setImporting(false);
    }
  };

  return (
    <Modal
      open={open}
      onCancel={handleClose}
      title="Import Technology Stack Version Master Data"
      footer={null}
      width={560}
      destroyOnHidden
    >
      <div className="py-3 space-y-4">
        {/* Template download */}
        <div className="flex items-center justify-end">
          <button
            className="flex items-center gap-1.5 text-xs text-primary-blue hover:underline"
            onClick={downloadTemplate}
          >
            <Download className="w-3 h-3" />
            Download Template
          </button>
        </div>

        {/* Drop zone */}
        <div
          className={`relative border-2 border-dashed rounded-lg flex flex-col items-center justify-center py-10 cursor-pointer transition-colors
            ${dragOver ? 'border-primary-blue bg-blue-50' : 'border-border-default hover:border-primary-blue'}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xls,.xlsx,.doc,.docx,.pdf"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }}
          />
          {file ? (
            <div className="flex items-center gap-2 text-sm text-text-primary" onClick={(e) => e.stopPropagation()}>
              <FileText className="w-5 h-5 text-primary-blue" />
              <span className="font-medium">{file.name}</span>
              <span className="text-text-secondary">({(file.size / 1024).toFixed(1)} KB)</span>
              <button
                className="ml-1 text-text-secondary hover:text-red-500"
                onClick={(e) => { e.stopPropagation(); setFile(null); setResult(null); if (inputRef.current) inputRef.current.value = ''; }}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <CloudUpload className="w-10 h-10 text-gray-300 mb-2" />
              <p className="text-sm text-text-secondary">
                Drag and drop the file here, or <span className="text-primary-blue cursor-pointer hover:underline">click to upload</span>
              </p>
              <p className="text-xs text-text-secondary mt-1">Supports Excel (.xlsx/.xls), CSV, Word (.docx), PDF formats</p>
            </>
          )}
        </div>

        {/* Result display */}
        {result && (
          <div className={`rounded p-3 text-sm ${result.failed > 0 ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
            <p className="font-medium mb-1">
              {result.failed > 0
                ? `Import completed with errors: ${result.success} succeeded, ${result.failed} failed`
                : `Successfully imported ${result.success} record(s)`}
            </p>
            {result.errors.map((e, i) => (
              <p key={i} className="text-xs text-red-600 mt-0.5">{e}</p>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-2 pt-2 border-t border-border-default">
          <button
            className="px-4 py-1.5 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary"
            onClick={handleClose}
            disabled={importing}
          >
            Cancel
          </button>
          <button
            className="px-4 py-1.5 text-sm bg-primary-blue text-white rounded hover:bg-blue-700 disabled:opacity-50"
            onClick={handleConfirm}
            disabled={!file || importing}
          >
            {importing ? 'Importing...' : 'Confirm Import'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ── Page ───────────────────────────────────────────────────────

export default function TechStackMasterDataPage() {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const canWriteTechStack = hasRole('ea_admin');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [searchInitialValues, setSearchInitialValues] = useState<Record<string, string>>({});
  const [importOpen, setImportOpen] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  // Add new sorting state
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

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
    if (!selectedCategories.length) {
      return [];
    }
    return all
      .filter((o) => selectedCategories.includes(o.category))
      .map((o) => ({ label: o.label, value: o.value }));
  }, [categoryData, selectedCategories]);

  const searchFields: SearchField[] = [
    { key: 'category', label: 'Category', type: 'multiselect', options: categoryOptions },
    { key: 'subCategory', label: 'Sub-Category', type: 'multiselect', options: subCategoryOptions },
    { key: 'eaAdvice', label: 'EA Advice', type: 'multiselect', options: EA_ADVICE_OPTIONS },
    { key: 'component', label: 'Technology Component', type: 'text', placeholder: 'Technology Component' },
    { key: 'componentPackage', label: 'Component Package Name', type: 'text', placeholder: 'Component Package Name' },
  ];

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerRecordId, setDrawerRecordId] = useState<string | undefined>(undefined);

  // Delete confirm state
  const [deleteTarget, setDeleteTarget] = useState<MasterRecord | null>(null);
  const [deleting, setDeleting] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['techStackMaster', page, pageSize, filters, sortKey, sortDir],
    queryFn: () => api.get<any>('/technology-stack', {
      page,
      pageSize,
      ...filters,
      sortField: sortKey || undefined,
      sortOrder: sortDir || undefined,
    }),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['techStackMaster'] });

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.delete(`/technology-stack/${deleteTarget.id}`);
      refresh();
      setDeleteTarget(null);
    } catch {
      // keep dialog open on error
    } finally {
      setDeleting(false);
    }
  };

  // ── columns ──────────────────────────────────────────────────
  const columns: Column<MasterRecord>[] = [
    { key: 'masterNo', title: 'No.', sortable: true, width: 90, pinned: 'left' },
    { key: 'category', title: 'Category', sortable: true },
    { key: 'sourceType', title: 'Source Type', sortable: true },
    { key: 'source', title: 'Source', sortable: true },
    { key: 'subCategory', title: 'Sub Category', sortable: true },
    { key: 'component', title: 'Technology Component', sortable: true },
    { key: 'componentPackage', title: 'Component Package Name', sortable: true },
    { key: 'version', title: 'Version', sortable: true },
    { key: 'eaAdvice', title: 'EA Advice', sortable: true },
    { key: 'standard', title: 'Standard', sortable: true },
    { key: 'eolDate', title: 'EOL Date', sortable: true },
    {
      key: 'operation',
      title: 'Operation',
      sortable: false,
      width: 120,
      pinned: 'right',
      render: (_v, record) =>
        canWriteTechStack ? (
          <div className="flex items-center gap-2">
            <button
              className="text-text-secondary hover:text-primary-blue"
              onClick={(e) => {
                e.stopPropagation();
                setDrawerRecordId(record.id);
                setDrawerOpen(true);
              }}
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button
              className="text-text-secondary hover:text-red-500"
              onClick={(e) => {
                e.stopPropagation();
                setDeleteTarget(record);
              }}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : null,
    },
  ];

  // Sorting callback
  const handleSort = (key: string, direction: 'asc' | 'desc') => {
    setSortKey(key);
    setSortDir(direction);
    setPage(1);
  };

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-text-primary mb-4">
        Technology Stack Version Master Data
      </h1>

      <SearchForm
        initialValues={searchInitialValues}
        fields={searchFields}
        onSearch={(v) => {
          setFilters(v);
          setPage(1);
        }}
        onReset={() => {
          setFilters({});
          setSearchInitialValues({});
          setSelectedCategories([]);
          setPage(1);
        }}
        onChange={(key, _value, allValues) => {
          if (key === 'category') {
            const categories = (allValues.category || '')
              .split(',')
              .map((v) => v.trim())
              .filter(Boolean);
            setSelectedCategories(categories);

            const allowedSubCategoryValues = new Set(
              ((categoryData?.subCategories ?? []) as Array<{ category: string; label: string; value: string }>)
                .filter((o) => categories.includes(o.category))
                .map((o) => o.value)
            );

            const currentSubCategoryValues = (allValues.subCategory || '')
              .split(',')
              .map((v) => v.trim())
              .filter(Boolean);

            const nextSubCategoryValues = currentSubCategoryValues
              .filter((v) => allowedSubCategoryValues.has(v));

            const nextSubCategory = nextSubCategoryValues.join(',');
            if ((allValues.subCategory || '') !== nextSubCategory) {
              setSearchInitialValues({
                ...allValues,
                subCategory: nextSubCategory,
              });
            }
          }
        }}
      />

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-3">
        {canWriteTechStack && (
          <>
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary-blue border border-primary-blue rounded hover:bg-blue-50"
              onClick={() => { setDrawerRecordId(undefined); setDrawerOpen(true); }}
            >
              <Plus className="w-3.5 h-3.5" />
              New
            </button>
            <button
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-border-default rounded hover:bg-gray-50 text-text-secondary"
              onClick={() => setImportOpen(true)}
            >
              <Upload className="w-3.5 h-3.5" />
              Import
            </button>
          </>
        )}
        <ExportButton
          entity="technology-stack"
          label="Export CSV"
          params={filters as Record<string, string>}
        />
      </div>

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        rowKey="id"
        loading={isLoading}
        showColumnSettings
        onSort={handleSort}
        sortKey={sortKey}
        sortDirection={sortDir}
      />
      {data && (
        <Pagination
          currentPage={page}
          totalPages={data.totalPages || 1}
          totalItems={data.total || 0}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => {
            setPageSize(s);
            setPage(1);
          }}
        />
      )}

      {/* Master Data Drawer */}
      {drawerOpen && (
        <MasterDataDrawer
          recordId={drawerRecordId}
          onClose={() => setDrawerOpen(false)}
          onSaved={() => { setDrawerOpen(false); refresh(); }}
        />
      )}

      {/* Import Modal */}
      <ImportModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onSuccess={() => { refresh(); setImportOpen(false); }}
      />

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleting}
        variant="danger"
        title="Delete Record"
        message={
          <>
            Are you sure you want to delete{' '}
            <strong>
              {deleteTarget?.component} {deleteTarget?.version}
            </strong>
            ?
            <br />
            This action cannot be undone.
          </>
        }
        confirmLabel="Delete"
      />
    </div>
  );
}