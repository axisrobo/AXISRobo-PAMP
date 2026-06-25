import { Database, Settings, Users } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const dataManagementNav: ModuleNavDefinition = {
  key: 'data_management',
  navItems: [
    {
      label: 'Data Management',
      href: '/data-privacy',
      icon: Database,
      children: [
        {
          label: 'Data Privacy',
          href: '/data-privacy',
          icon: Database,
        },
        {
          label: 'Help',
          href: '/help',
          icon: Database,
        },
      ],
    },
    {
      label: 'System Management',
      href: '/users',
      icon: Settings,
      children: [
        {
          label: 'User Management',
          href: '/users',
          icon: Users,
        },
        {
          label: 'Resources',
          href: '/resources',
          icon: Settings,
          requiredResource: 'resource',
          requiredScope: 'read',
        },
        {
          label: 'Certification',
          href: '/certification',
          icon: Settings,
        },
        {
          label: 'Master Data',
          href: '/master-data',
          icon: Settings,
        },
      ],
    },
  ],
};
