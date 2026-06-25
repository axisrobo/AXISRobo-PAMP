import { FolderKanban, PlusCircle } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const projectManagementNav: ModuleNavDefinition = {
  key: 'project_management',
  navItems: [
    {
      label: 'Projects',
      href: '/projects',
      icon: FolderKanban,
      requiredResource: 'project',
      requiredScope: 'read',
      children: [
        {
          label: 'Project List',
          href: '/projects',
          icon: FolderKanban,
          requiredResource: 'project',
          requiredScope: 'read',
        },
        {
          label: 'Create Project',
          href: '/projects/new',
          icon: PlusCircle,
          requiredResource: 'project',
          requiredScope: 'write',
        },
      ],
    },
  ],
};
