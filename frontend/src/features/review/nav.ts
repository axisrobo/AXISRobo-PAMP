import { Boxes, ClipboardList, FileText, ShieldCheck } from 'lucide-react';
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
        {
          label: 'AI Self-Assessment',
          href: '/ai-assessment',
          icon: ShieldCheck,
          requiredRole: 'ea_admin',
        },
        {
          label: 'AI Model Registry',
          href: '/ai-models',
          icon: Boxes,
          requiredRole: 'ea_admin',
        },
      ],
    },
  ],
};
