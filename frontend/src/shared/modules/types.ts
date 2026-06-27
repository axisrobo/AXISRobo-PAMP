import type { NavItem } from '@/shared/lib/constants';

export type FrontendModuleKey =
  | 'architecture_review'
  | 'ai_management'
  | 'add'
  | 'application_management'
  | 'data_management'
  | 'project_management'
  | 'technology_stack_management';

export interface ModuleNavDefinition {
  key: FrontendModuleKey | 'core';
  navItems: NavItem[];
}
