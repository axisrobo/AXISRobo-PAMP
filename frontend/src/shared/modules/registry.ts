import type { NavItem } from '@/shared/lib/constants';
import type { FrontendModuleKey, ModuleNavDefinition } from '@/shared/modules/types';
import { coreNav } from '@/features/core/nav';
import { architectureReviewNav } from '@/features/review/nav';
import { addNav } from '@/features/add/nav';
import { applicationManagementNav } from '@/features/portfolio/nav';
import { dataManagementNav } from '@/features/data-management/nav';
import { projectManagementNav } from '@/features/projects/nav';
import { technologyStackManagementNav } from '@/features/tech-stack/nav';
import { enabledModules } from '@/shared/modules/config';

const MODULE_NAV_REGISTRY: Record<FrontendModuleKey, ModuleNavDefinition> = {
  architecture_review: architectureReviewNav,
  add: addNav,
  application_management: applicationManagementNav,
  data_management: dataManagementNav,
  project_management: projectManagementNav,
  technology_stack_management: technologyStackManagementNav,
};

export function getEnabledSidebarItems(): NavItem[] {
  const navItems: NavItem[] = [...coreNav.navItems];

  for (const moduleKey of Object.keys(MODULE_NAV_REGISTRY) as FrontendModuleKey[]) {
    if (!enabledModules.has(moduleKey)) {
      continue;
    }
    navItems.push(...MODULE_NAV_REGISTRY[moduleKey].navItems);
  }

  return navItems;
}
