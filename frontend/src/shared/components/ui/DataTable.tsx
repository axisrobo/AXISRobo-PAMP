'use client';

import { useState, useMemo } from 'react';
import type { Key } from 'react';
import { Table, Empty } from 'antd';
import type { TableProps } from 'antd';
import type { ColumnType } from 'antd/es/table';
import { Settings2, Download } from 'lucide-react';
import { useT } from '@/shared/lib/locale';
import { fetchBlob } from '@/shared/lib/api';
import { Resizable } from 'react-resizable';
// Removed: import 'react-resizable/css/styles.css';

export interface Column<T> {
  key: string;
  title: React.ReactNode;
  width?: number | string;
  sortable?: boolean;
  pinned?: 'left' | 'right';
  hidden?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
}

const ResizableTitle = (props: any) => {
  const { onResize, width, ...restProps } = props;

  if (!width) {
    return <th {...restProps} />;
  }

  return (
    <Resizable
      width={width}
      height={0}
      handle={
        <span
          className="react-resizable-handle"
          onClick={(e) => {
            e.stopPropagation();
          }}
        />
      }
      onResize={onResize}
      draggableOpts={{ enableUserSelectHack: false }}
    >
      <th {...restProps} />
    </Resizable>
  );
};

export interface ExportConfig {
  /** Backend entity name, e.g. "bcm", "projects", "meetings" */
  entity: string;
  /** Current search filters — forwarded as query params to /api/export/:entity */
  params?: Record<string, string>;
  /** Button label, defaults to "Export CSV" */
  label?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: string | ((record: T) => Key);
  loading?: boolean;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  onRowClick?: (record: T) => void;
  emptyText?: string;
  showColumnSettings?: boolean;
  /** Pass this to show an Export button in the table toolbar */
  exportConfig?: ExportConfig;
  /** antd Table pagination config — pass false to disable built-in pagination */
  pagination?: TableProps<T>['pagination'] | false;
  /** antd Table rowSelection config — enables checkbox column */
  rowSelection?: TableProps<T>['rowSelection'];
  /** Render card-based list instead of table on screens < 768px */
  mobileView?: 'cards' | undefined;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

/** Convert project Column<T> to antd ColumnType<T> */
function toAntdColumns<T extends Record<string, any>>(
  columns: Column<T>[],
  hiddenColumns: Set<string>,
  columnWidths: Record<string, number>,
  handleResize: (key: string) => (e: any, data: any) => void,
  sortKey?: string,
  sortDirection?: 'asc' | 'desc',
  t: (s: string) => string = (s) => s,
): ColumnType<T>[] {
  return columns
    .filter((col) => !col.hidden && !hiddenColumns.has(col.key))
    .map((col) => {
      const width = columnWidths[col.key] || (typeof col.width === 'number' ? col.width : (parseInt(col.width as string) || 150));
      const antdCol: any = {
        key: col.key,
        dataIndex: col.key,
        title: typeof col.title === 'string' ? t(col.title) : col.title,
        width,
        fixed: col.pinned || undefined,
        ellipsis: {
          showTitle: true,
        },
        onHeaderCell: (column: any) => ({
          width: column.width,
          onResize: handleResize(col.key),
        }),
      };
      if (col.sortable) {
        antdCol.sorter = true;
        antdCol.sortDirections = ['ascend', 'descend', 'ascend'];
        if (sortKey === col.key) {
          antdCol.sortOrder = sortDirection === 'asc' ? 'ascend' : 'descend';
        } else {
          antdCol.sortOrder = null;
        }
      }
      if (col.render) {
        const originalRender = col.render;
        antdCol.render = (value: any, record: T, index: number) =>
          originalRender(value, record, index);
      }
      return antdCol;
    });
}

export function DataTable<T extends Record<string, any>>({
  columns: initialColumns,
  data,
  rowKey,
  loading = false,
  onSort,
  sortKey,
  sortDirection,
  onRowClick,
  emptyText = 'No data',
  showColumnSettings = false,
  exportConfig,
  pagination = false,
  rowSelection,
  mobileView,
}: DataTableProps<T>) {
  const t = useT();
  const [columnSettingsOpen, setColumnSettingsOpen] = useState(false);
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});

  const handleResize = (key: string) => (e: any, { size }: any) => {
    setColumnWidths((prev) => ({
      ...prev,
      [key]: size.width,
    }));
  };

  const antdColumns = useMemo(() => 
    toAntdColumns(initialColumns, hiddenColumns, columnWidths, handleResize, sortKey, sortDirection, t),
    [initialColumns, hiddenColumns, columnWidths, sortKey, sortDirection, t]
  );
  const computedRowKey = useMemo(() => {
    const keyCounts = new Map<Key, number>();

    data.forEach((record, i) => {
      const rawKey = typeof rowKey === 'function' ? rowKey(record) : record[rowKey];
      const normalizedKey = rawKey ?? `row-${i}`;
      keyCounts.set(normalizedKey, (keyCounts.get(normalizedKey) ?? 0) + 1);
    });

    return (record: T) => {
      const rawKey = typeof rowKey === 'function' ? rowKey(record) : record[rowKey];
      const i = data.indexOf(record);
      const normalizedKey = rawKey ?? `row-${i}`;

      if ((keyCounts.get(normalizedKey) ?? 0) > 1) {
        return `${String(normalizedKey)}-${i}`;
      }

      return normalizedKey;
    };
  }, [data, rowKey]);
  const hasPinned = initialColumns.some((c: Column<T>) => c.pinned);

  const toggleColumn = (key: string) => {
    setHiddenColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const handleExport = async () => {
    if (!exportConfig) return;
    setExporting(true);
    try {
      const { entity, params } = exportConfig;
      
      let exportUrl = '';
      let fileExtension = 'csv';
      
      // Use standard export router for common entities, or custom ones if defined
      if (entity === 'bcm') {
        exportUrl = `${API_BASE}/applications/bcm/export`;
        fileExtension = 'xlsx';
      } else {
        exportUrl = `${API_BASE}/export/${entity}`;
      }

      const query =
        params && Object.keys(params).length
          ? '?' +
            new URLSearchParams(
              Object.fromEntries(Object.entries(params).filter(([, v]) => v))
            ).toString()
          : '';

      const blob = await fetchBlob(`${exportUrl}${query}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entity}-export-${new Date().getTime()}.${fileExtension}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  const showToolbar = showColumnSettings || !!exportConfig;

  const visibleColumns = useMemo(
    () => initialColumns.filter((col) => !col.hidden && !hiddenColumns.has(col.key)),
    [initialColumns, hiddenColumns]
  );

  const resolveRowKey = (record: T, index: number): Key => {
    const rawKey = typeof rowKey === 'function' ? rowKey(record) : record[rowKey];
    return rawKey ?? `row-${index}`;
  };

  const mobileCards = mobileView === 'cards' && (
    <div className="md:hidden space-y-3">
      {data.length === 0 && !loading && (
        <div className="py-8 text-center text-sm text-text-secondary">{emptyText}</div>
      )}
      {data.map((record, idx) => (
        <div
          key={resolveRowKey(record, idx)}
          className="bg-white rounded-lg border border-border-light p-4 shadow-sm"
          onClick={onRowClick ? () => onRowClick(record) : undefined}
          style={onRowClick ? { cursor: 'pointer' } : undefined}
        >
          {visibleColumns.map((col) => {
            const rawValue = record[col.key];
            const rendered = col.render
              ? col.render(rawValue, record, idx)
              : rawValue != null
                ? String(rawValue)
                : '-';
            return (
              <div key={col.key} className="flex justify-between py-1 text-sm">
                <span className="text-text-secondary shrink-0 mr-2">
                  {typeof col.title === 'string' ? t(col.title) : col.title}
                </span>
                <span className="text-text-primary text-right break-all">{rendered}</span>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );

  const handleTableChange: TableProps<T>['onChange'] = (_pagination, _filters, sorter) => {
    if (!onSort) return;
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    if (s?.columnKey) {
      if (s.order === 'ascend') {
        onSort(s.columnKey as string, 'asc');
      } else if (s.order === 'descend') {
        onSort(s.columnKey as string, 'desc');
      } else {
        // When s.order is undefined (the 3rd click), reset to 'asc'
        onSort(s.columnKey as string, 'asc');
      }
    }
  };

  return (
    <div className="relative">
      {showToolbar && (
        <div className="flex justify-end items-center gap-2 mb-2">
          {exportConfig && (
            <button
              onClick={handleExport}
              disabled={exporting}
              aria-label={exportConfig.label ?? t('Export')}
              className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary px-2 py-1 rounded hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {exporting ? t('Loading...') : (exportConfig.label ?? t('Export'))}
            </button>
          )}

          {showColumnSettings && (
            <div className="relative">
              <button
                onClick={() => setColumnSettingsOpen(!columnSettingsOpen)}
                aria-label={t('Column Settings')}
                className="flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary px-2 py-1 rounded hover:bg-gray-50 transition-colors"
              >
                <Settings2 className="w-4 h-4" />
                {t('Column Settings')}
              </button>
              {columnSettingsOpen && (
                <div className="absolute right-0 top-8 z-20 bg-white border border-border-light rounded-lg shadow-lg p-3 min-w-[200px]">
                  <div className="text-sm font-medium mb-2">{t('Column Settings')}</div>
                  {initialColumns.map((col: Column<T>) => (
                    <label key={col.key} className="flex items-center gap-2 py-1 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!hiddenColumns.has(col.key)}
                        onChange={() => toggleColumn(col.key)}
                        className="rounded"
                      />
                      {typeof col.title === 'string' ? t(col.title) : col.title}
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {mobileCards}

      <div className={mobileView === 'cards' ? 'hidden md:block' : ''}>
        <Table<T>
          components={{
            header: {
              cell: ResizableTitle,
            },
          }}
          columns={antdColumns}
          dataSource={data}
          rowKey={computedRowKey}
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
          onRow={onRowClick ? (record) => ({ onClick: () => onRowClick(record), style: { cursor: 'pointer' } }) : undefined}
          locale={{ emptyText: <Empty description={emptyText} /> }}
          size="small"
          scroll={{ x: 1 }}
          tableLayout="fixed"
          rowClassName={(_record, index) => (index % 2 === 1 ? 'bg-[#fafafa]' : '')}
          rowSelection={rowSelection}
        />
      </div>
    </div>
  );
}
