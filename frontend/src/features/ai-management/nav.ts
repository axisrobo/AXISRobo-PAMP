import { Bot, Boxes, Server, ShieldCheck, Sparkles } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const aiManagementNav: ModuleNavDefinition = {
  key: 'ai_management',
  navItems: [
    {
      label: 'AI Management',
      href: '/ai-assessment',
      icon: Sparkles,
      requiredRole: 'ea_admin',
      children: [
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
        {
          label: 'Agent Registry',
          href: '/ai-agents',
          icon: Bot,
          requiredRole: 'ea_admin',
        },
        {
          label: 'MCP Governance',
          href: '/mcp-servers',
          icon: Server,
          requiredRole: 'ea_admin',
        },
      ],
    },
  ],
};
