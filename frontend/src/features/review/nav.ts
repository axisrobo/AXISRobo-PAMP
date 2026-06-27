import { ClipboardList, FileText } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const architectureReviewNav: ModuleNavDefinition = {
  key: 'architecture_review',
  navItems: [
    {
      label: 'EA Review',
      href: '/',
      icon: ClipboardList,
      requiredResource: 'ea_request',
      requiredScope: 'read',
      children: [
        {
          label: 'Requests',
          href: '/',
          icon: FileText,
          requiredResource: 'ea_request',
          requiredScope: 'read',
        },
        {
          label: 'Create Request',
          href: '/ea-review/request/create',
          icon: ClipboardList,
          requiredResource: 'ea_request',
          requiredScope: 'read',
        },
      ],
    },
  ],
};
