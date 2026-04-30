// Hierarchical agency filter for user management
import { Agency } from '@/app/types';
import { CurrentUser } from '@/app/hooks/use-current-user';
import { UserRole } from '@/app/types';

/**
 * Get accessible agencies based on current user's hierarchical level
 * 
 * Hierarchy:
 * - ACI/DINT (central) → sees ALL agencies
 * - ARI (regional) → sees only their child ALI agencies
 * - ALI (local) → sees only their own agency
 */
export function getAccessibleAgencies(currentUser: CurrentUser | null, agencies: Agency[]): Agency[] {
  if (!currentUser || agencies.length === 0) return [];

  const userAgencyType = currentUser.agency_type;

  // Central admin sees all
  if (userAgencyType === 'central' || currentUser.role === 'admin') {
    return agencies;
  }

  // Regional sees only their child agencies (type: 'local')
  if (userAgencyType === 'regional') {
    return agencies.filter(
      (agency) => agency.parent_agency_id === currentUser.agency_id
    );
  }

  // Local agency sees only themselves
  return agencies.filter((agency) => agency.id === currentUser.agency_id);
}

/**
 * Get allowed roles based on current user's hierarchical level
 * 
 * Rules:
 * - admin/central: all roles
 * - regional: intelligence, supervisor, field_agent (no admin)
 * - local: only field_agent
 */
export function getAllowedRoles(currentUser: CurrentUser | null): UserRole[] {
  if (!currentUser) return ['field_agent'];

  const userAgencyType = currentUser.agency_type;

  if (userAgencyType === 'central' || currentUser.role === 'admin') {
    return ['intelligence', 'field_agent', 'supervisor', 'admin'];
  }

  if (userAgencyType === 'regional') {
    return ['intelligence', 'field_agent', 'supervisor'];
  }

  // Local can only create field agents
  return ['field_agent'];
}

/**
 * Get role display name in Portuguese
 */
export function getRoleLabel(role: UserRole): string {
  const labels: Record<UserRole, string> = {
    intelligence: 'Analista de Inteligência',
    field_agent: 'Agente de Campo',
    supervisor: 'Supervisor',
    admin: 'Administrador',
  };
  return labels[role] || role;
}

/**
 * Get agency type label in Portuguese
 */
export function getAgencyTypeLabel(type: Agency['type']): string {
  const labels: Record<Agency['type'], string> = {
    central: 'ACI/DINT',
    regional: 'ARI',
    local: 'ALI',
  };
  return labels[type] || type;
}