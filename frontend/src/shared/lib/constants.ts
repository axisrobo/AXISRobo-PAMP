export interface NavItem {
  label: string;
  href: string;
  icon: any;
  children?: NavItem[];
  /** Required permission resource (e.g. "settings"). If omitted, visible to all. */
  requiredResource?: string;
  /** Required permission scope (default: "read") */
  requiredScope?: string;
  /** Required role (e.g. "ea_reviewer"). If set, only users with this role (or ea_admin) see the item. */
  requiredRole?: string;
}

export const statusColors: Record<string, string> = {
  Completed: 'text-status-completed',
  'In Progress': 'text-status-in-progress',
  Submitted: 'text-status-submitted',
  Draft: 'text-status-draft',
  'Accepted by EA': 'text-status-accepted',
  Approved: 'text-status-completed',
  'Approved with Actions': 'text-status-completed',
  Rejected: 'text-red-500',
  Open: 'text-status-in-progress',
  'In Validation': 'text-status-submitted',
  Closed: 'text-status-completed',
  Available: 'text-status-completed',
  Booked: 'text-status-submitted',
  Expired: 'text-status-draft',
};

export const statusBgColors: Record<string, string> = {
  Completed: 'bg-green-50 text-status-completed',
  'In Progress': 'bg-orange-50 text-status-in-progress',
  Submitted: 'bg-blue-50 text-status-submitted',
  Draft: 'bg-gray-50 text-status-draft',
  'Accepted by EA': 'bg-purple-50 text-status-accepted',
  Approved: 'bg-green-50 text-status-completed',
  Open: 'bg-orange-50 text-status-in-progress',
  Closed: 'bg-green-50 text-status-completed',
};
