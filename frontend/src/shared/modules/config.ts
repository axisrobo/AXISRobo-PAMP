import type { FrontendModuleKey } from '@/shared/modules/types';

const DEFAULT_ENABLED_MODULES: FrontendModuleKey[] = [
  'architecture_review',
  'ai_management',
  'add',
  'application_management',
  'data_management',
  'project_management',
  'technology_stack_management',
];

const MODULE_KEYS = new Set<FrontendModuleKey>(DEFAULT_ENABLED_MODULES);

export function parseEnabledModules(rawValue: string | undefined): Set<FrontendModuleKey> {
  if (!rawValue || !rawValue.trim()) {
    return new Set(DEFAULT_ENABLED_MODULES);
  }

  const values = rawValue
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  const enabled = new Set<FrontendModuleKey>();
  for (const value of values) {
    if (MODULE_KEYS.has(value as FrontendModuleKey)) {
      enabled.add(value as FrontendModuleKey);
    }
  }

  if (enabled.size === 0) {
    return new Set(DEFAULT_ENABLED_MODULES);
  }

  return enabled;
}

export const enabledModules = parseEnabledModules(process.env.NEXT_PUBLIC_ENABLED_MODULES);

export function isModuleEnabled(moduleKey: FrontendModuleKey): boolean {
  return enabledModules.has(moduleKey);
}
