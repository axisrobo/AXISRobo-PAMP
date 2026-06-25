'use client';

import { Pagination as AntdPagination } from 'antd';
import { useT } from '@/shared/lib/locale';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

const pageSizeOptions = [10, 20, 50, 100];

export function Pagination({
  currentPage,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const t = useT();

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-border-light bg-white">
      <div className="text-sm text-text-secondary">
        {t('Total')} {totalItems} {t('items')}
      </div>
      <AntdPagination
        current={currentPage}
        total={totalItems}
        pageSize={pageSize}
        pageSizeOptions={pageSizeOptions}
        showSizeChanger
        onChange={(page, size) => {
          if (size !== pageSize) {
            onPageSizeChange(size);
          }
          if (page !== currentPage) {
            onPageChange(page);
          }
        }}
        size="small"
      />
    </div>
  );
}
