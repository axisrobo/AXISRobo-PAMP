import { AppWindow, Building2 } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const applicationManagementNav: ModuleNavDefinition = {
  key: 'application_management',
  navItems: [
    {
      label: 'Business Capability',
      href: '/app-management/bcm',
      icon: Building2,
      children: [
        { label: 'Business Capability Mapping', href: '/app-management/bcm', icon: Building2 },
        { label: 'BizCapability Master Data', href: '/app-management/biz-capability', icon: Building2 },
        { label: 'Business Capability Analysis', href: '/app-management/bc-visualization', icon: Building2 },
      ],
    },
    {
      label: 'Application Management',
      href: '/app-management/cmdb',
      icon: AppWindow,
      children: [
        { label: 'Applications', href: '/app-management/cmdb', icon: AppWindow },
      ],
    },
  ],
};
