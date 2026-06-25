/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect, useCallback } from 'react';
import { Input, Button, Pagination, Checkbox } from 'antd';
import { X } from 'lucide-react';
import { api } from '@/shared/lib/api';

interface ResourcePoolItem {
  itcode: string;
  name: string;
  workerType: string;
  managerItcode: string;
}

interface Props {
  onClose: () => void;
  onConfirm: (selected: ResourcePoolItem[]) => void;
}

export function ResourcePoolPickerModal({ onClose, onConfirm }: Props) {
  const [itcodeInput, setItcodeInput] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [items, setItems] = useState<ResourcePoolItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<ResourcePoolItem[]>([]);

  const fetchData = useCallback(
    async (filters: { itcode: string; name: string }, p: number) => {
      setLoading(true);
      try {
        const params: Record<string, any> = { page: p, pageSize };
        if (filters.itcode) params.itcode = filters.itcode;
        if (filters.name) params.name = filters.name;
        const res: any = await api.get<any>('/technology-stack/resource-pool', params);
        setItems(res.items ?? []);
        setTotal(res.total ?? 0);
        setPage(p);
      } catch {
        setItems([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    },
    [pageSize],
  );

  // load first page on mount
  useEffect(() => {
    fetchData({ itcode: '', name: '' }, 1);
  }, [fetchData]);

  function handleSearch() {
    fetchData({ itcode: itcodeInput, name: nameInput }, 1);
  }

  function handleReset() {
    setItcodeInput('');
    setNameInput('');
    setSelected([]);
    fetchData({ itcode: '', name: '' }, 1);
  }

  function handlePageChange(p: number) {
    fetchData({ itcode: itcodeInput, name: nameInput }, p);
  }

  function toggleRow(item: ResourcePoolItem) {
    setSelected((prev) => {
      const exists = prev.some((s) => s.itcode === item.itcode);
      return exists ? prev.filter((s) => s.itcode !== item.itcode) : [...prev, item];
    });
  }

  function isChecked(itcode: string) {
    return selected.some((s) => s.itcode === itcode);
  }

  // Check all visible rows
  const allVisibleChecked =
    items.length > 0 && items.every((item) => isChecked(item.itcode));

  function toggleAll() {
    if (allVisibleChecked) {
      setSelected((prev) => prev.filter((s) => !items.some((i) => i.itcode === s.itcode)));
    } else {
      const toAdd = items.filter((i) => !isChecked(i.itcode));
      setSelected((prev) => [...prev, ...toAdd]);
    }
  }

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/40" role="dialog" aria-modal="true" aria-labelledby="resource-pool-title">
      <div className="bg-white rounded-lg shadow-xl w-[800px] max-w-[95vw] flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 id="resource-pool-title" className="text-base font-semibold text-gray-800">Select from Resource Pool</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {/* Search bar */}
        <div className="flex items-center gap-3 px-6 py-3 border-b">
          <Input
            placeholder="IT Code"
            value={itcodeInput}
            onChange={(e) => setItcodeInput(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 180 }}
            allowClear
          />
          <Input
            placeholder="Name"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 220 }}
            allowClear
          />
          <Button type="primary" onClick={handleSearch} loading={loading}>
            Search
          </Button>
          <Button onClick={handleReset}>Reset</Button>
          {selected.length > 0 && (
            <span className="text-xs text-blue-500 ml-2">{selected.length} selected</span>
          )}
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto px-6 py-2">
          <table className="w-full text-sm border-collapse">
            <thead className="sticky top-0 bg-gray-50 z-10">
              <tr className="text-gray-600">
                <th className="px-3 py-2 border-b w-10">
                  <Checkbox
                    checked={allVisibleChecked}
                    indeterminate={!allVisibleChecked && items.some((i) => isChecked(i.itcode))}
                    onChange={toggleAll}
                  />
                </th>
                {['IT Code', 'Name', 'Manager'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left font-medium border-b">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-10 text-gray-400">
                    No Data
                  </td>
                </tr>
              )}
              {loading && (
                <tr>
                  <td colSpan={4} className="text-center py-10 text-gray-400">
                    Loading...
                  </td>
                </tr>
              )}
              {!loading &&
                items.map((item) => (
                  <tr
                    key={item.itcode}
                    className="border-b border-gray-100 hover:bg-blue-50 cursor-pointer"
                    onClick={() => toggleRow(item)}
                  >
                    <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                      <Checkbox checked={isChecked(item.itcode)} onChange={() => toggleRow(item)} />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{item.itcode}</td>
                    <td className="px-3 py-2">{item.name}</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">{item.managerItcode}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-3 border-t">
          <span className="text-xs text-gray-500">Total {total} Items</span>
          <Pagination
            current={page}
            total={total}
            pageSize={pageSize}
            onChange={handlePageChange}
            showSizeChanger={false}
            size="small"
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t">
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="primary"
            disabled={selected.length === 0}
            onClick={() => onConfirm(selected)}
          >
            OK
          </Button>
        </div>
      </div>
    </div>
  );
}
