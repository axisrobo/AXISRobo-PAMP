import { ServerCog } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const technologyStackManagementNav: ModuleNavDefinition = {
  key: 'technology_stack_management',
  navItems: [
    {
      label: 'Technology Stack',
      href: '/tech-stack',
      icon: ServerCog,
      children: [
        { label: 'Lifecycle Management', href: '/tech-stack', icon: ServerCog },
        { label: 'Technology Stack Master Data', href: '/tech-stack/master-data', icon: ServerCog },
        { label: 'Platform Engineering', href: '/platform-engineering', icon: ServerCog },
      ],
    },
  ],
};
