import { User } from 'lucide-react';
import type { ModuleNavDefinition } from '@/shared/modules/types';

export const coreNav: ModuleNavDefinition = {
  key: 'core',
  navItems: [{ label: "I'm Requester", href: '/', icon: User }],
};
