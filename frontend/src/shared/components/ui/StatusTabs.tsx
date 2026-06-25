'use client';

import { Tabs, Badge } from 'antd';
import type { TabsProps } from 'antd';

interface StatusTab {
  label: string;
  value: string;
  count?: number;
}

interface StatusTabsProps {
  tabs: StatusTab[];
  activeTab: string;
  onTabChange: (value: string) => void;
}

export function StatusTabs({ tabs, activeTab, onTabChange }: StatusTabsProps) {
  const items: TabsProps['items'] = tabs.map((tab) => ({
    key: tab.value,
    label: (
      <span>
        {tab.label}
        {tab.count !== undefined && (
          <Badge
            count={tab.count}
            showZero
            size="small"
            style={{ marginLeft: 6 }}
            color={activeTab === tab.value ? '#4096FF' : '#8c8c8c'}
          />
        )}
      </span>
    ),
  }));

  return (
    <div className="mb-4">
      <Tabs
        activeKey={activeTab}
        onChange={onTabChange}
        items={items}
        size="small"
      />
    </div>
  );
}
