/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Input, Button, Radio, Pagination, Spin } from 'antd';
import { api } from '@/shared/lib/api';

interface CmdbApp {
  appId: string;
  applicationName: string;
  appFullName: string;
  applicationStatus: string;
  applicationOwnership: string;
  applicationClassification: string;
  functionValueChain: string;
  applicationItOwner: string;
  portfolioManagement: string;
  applicationSolutionType: string;
}

interface CmdbPickerModalProps {
  onClose: () => void;
  onConfirm: (app: CmdbApp) => void;
}

export function CmdbPickerModal({ onClose, onConfirm }: CmdbPickerModalProps) {
  const [appIdInput, setAppIdInput] = useState('');
  const [appNameInput, setAppNameInput] = useState('');
  const [items, setItems] = useState<CmdbApp[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [loading, setLoading] = useState(false);
  // Pending search params (used for pagination)
  const [activeFilter, setActiveFilter] = useState<{ appId: string; appName: string }>({ appId: '', appName: '' });
  const [selected, setSelected] = useState<CmdbApp | null>(null);

  // Auto-fetch all on mount
  useEffect(() => {
    fetchData({ appId: '', appName: '' }, 1);
   
  }, []);

  async function fetchData(filter: { appId: string; appName: string }, targetPage: number) {
    setLoading(true);
    try {
      const params: Record<string, any> = { page: targetPage, pageSize };
      if (filter.appId) params.appId = filter.appId;
      if (filter.appName) params.appName = filter.appName;
      const res = await api.get<any>('/technology-stack/cmdb-lookup', params);
      setItems(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    const filter = { appId: appIdInput.trim(), appName: appNameInput.trim() };
    setActiveFilter(filter);
    setSelected(null);
    setPage(1);
    fetchData(filter, 1);
  }

  function handleReset() {
    setAppIdInput('');
    setAppNameInput('');
    const empty = { appId: '', appName: '' };
    setActiveFilter(empty);
    setSelected(null);
    setPage(1);
    fetchData(empty, 1);
  }

  function handlePageChange(newPage: number) {
    setPage(newPage);
    fetchData(activeFilter, newPage);
  }

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/40" role="dialog" aria-modal="true" aria-labelledby="cmdb-picker-title">
      <div className="bg-white rounded-lg shadow-xl w-[900px] max-w-[95vw] flex flex-col" style={{ maxHeight: '80vh' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 id="cmdb-picker-title" className="text-base font-semibold text-gray-800">Applications from CMDB</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search bar */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex items-center gap-3 flex-wrap">
            <Input
              placeholder="Application ID"
              value={appIdInput}
              onChange={e => setAppIdInput(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 180 }}
              allowClear
            />
            <Input
              placeholder="Application Name"
              value={appNameInput}
              onChange={e => setAppNameInput(e.target.value)}
              onPressEnter={handleSearch}
              style={{ width: 220 }}
              allowClear
            />
            <Button type="primary" onClick={handleSearch}>Search</Button>
            <Button onClick={handleReset}>Reset</Button>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto px-6 py-3">
          {loading ? (
            <div className="flex items-center justify-center py-12"><Spin /></div>
          ) : items.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-gray-400 text-sm">No results found</div>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="w-8 px-3 py-2.5"></th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Application ID</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Name</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Full Name</th>
                  <th className="px-3 py-2.5 text-left font-medium text-gray-600">Current Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr
                    key={item.appId}
                    className={`border-b border-gray-100 cursor-pointer hover:bg-blue-50 transition-colors ${selected?.appId === item.appId ? 'bg-blue-50' : ''}`}
                    onClick={() => setSelected(item)}
                  >
                    <td className="px-3 py-2.5 text-center">
                      <Radio checked={selected?.appId === item.appId} onChange={() => setSelected(item)} />
                    </td>
                    <td className="px-3 py-2.5 text-gray-800">{item.appId}</td>
                    <td className="px-3 py-2.5 text-gray-700">{item.applicationName}</td>
                    <td className="px-3 py-2.5 text-gray-700">{item.appFullName || item.applicationName}</td>
                    <td className="px-3 py-2.5 text-gray-600">{item.applicationStatus}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className="px-6 py-3 border-t bg-gray-50 flex items-center justify-between">
            <span className="text-sm text-gray-500">Total {total} Items</span>
            <Pagination
              current={page}
              total={total}
              pageSize={pageSize}
              onChange={handlePageChange}
              showSizeChanger={false}
              size="small"
            />
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <Button onClick={onClose}>Cancel</Button>
          <Button type="primary" disabled={!selected} onClick={() => selected && onConfirm(selected)}>OK</Button>
        </div>
      </div>
    </div>
  );
}
