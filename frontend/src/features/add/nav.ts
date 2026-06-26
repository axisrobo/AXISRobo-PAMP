import { Database, GitBranch, Layers3, Network } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const addNav: ModuleNavDefinition = {
  key: 'add',
  navItems: [
    {
      label: 'Architecture Decision & Design',
      href: '/questionnaire-config',
      icon: Network,
      requiredRole: 'ea_admin',
      children: [
        {
          label: 'Questionnaire Config',
          href: '/questionnaire-config',
          icon: Database,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Concern Mapping Config',
          href: '/concern-mapping-config',
          icon: GitBranch,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Concern Catalog',
          href: '/pact-concern-catalog',
          icon: Database,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Viewpoint Catalog',
          href: '/viewpoint-catalog',
          icon: Network,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Architecture Artifact Catalog',
          href: '/architecture-artifact-catalog',
          icon: Layers3,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Concern-Viewpoint Mapping',
          href: '/concern-viewpoint-mapping',
          icon: GitBranch,
          requiredRole: 'ea_admin',
        },
        {
          label: 'Viewpoint-Artifact Mapping',
          href: '/viewpoint-artifact-mapping',
          icon: Network,
          requiredRole: 'ea_admin',
        },
      ],
    },
  ],
};
