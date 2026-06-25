'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { useT } from '@/shared/lib/locale';
import { CapabilityMindmap, AppDashboard, CapabilityDashboard } from '@/features/portfolio/components/bc-visualization';
import type { DataState } from '@/features/portfolio/components/bc-visualization';
import { Map, LayoutGrid, Layers } from 'lucide-react';

type TabKey = 'mindmap' | 'applications' | 'capabilities';

export default function BCVisualizationPage() {
  const t = useT();
  const [activeTab, setActiveTab] = useState<TabKey>('capabilities');

  const { data, isLoading, error } = useQuery<DataState>({
    queryKey: ['bcm-visualization'],
    queryFn: () => api.get<DataState>('/applications/bcm/visualization'),
  });

  const tabs: { key: TabKey; label: string; icon: typeof Map }[] = [
    { key: 'capabilities', label: t('Capabilities'), icon: Layers },
    { key: 'applications', label: t('Applications'), icon: LayoutGrid },
    { key: 'mindmap', label: t('Capability Mindmap'), icon: Map },
  ];

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-lg font-semibold text-text-primary mb-4">{t('Business Capability Analysis')}</h1>
        <div className="flex items-center justify-center h-64">
          <div className="text-sm text-text-secondary">{t('Loading...')}</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <h1 className="text-lg font-semibold text-text-primary mb-4">{t('Business Capability Analysis')}</h1>
        <div className="flex items-center justify-center h-64">
          <div className="text-sm text-red-500">Failed to load visualization data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-text-primary">{t('Business Capability Analysis')}</h1>
        <div className="text-xs text-text-secondary">
          {data.capabilities.length} {t('capabilities')} &middot; {data.applications.length} {t('applications')} &middot; {data.mappings.length} {t('mappings')}
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex items-center gap-1 mb-4 border-b border-gray-200">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.key
                  ? 'text-primary-blue border-primary-blue'
                  : 'text-text-secondary border-transparent hover:text-text-primary hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === 'mindmap' && (
        <CapabilityMindmap
          capabilities={data.capabilities}
          domains={data.domains}
        />
      )}
      {activeTab === 'applications' && (
        <AppDashboard applications={data.applications} capabilities={data.capabilities} />
      )}
      {activeTab === 'capabilities' && (
        <CapabilityDashboard
          capabilities={data.capabilities}
          domains={data.domains}
          applications={data.applications}
        />
      )}
    </div>
  );
}

