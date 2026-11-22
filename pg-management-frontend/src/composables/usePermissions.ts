import { useAuthStore } from '@/stores/auth'
import type { DocType, PermType, PgRole } from '@/types'

/**
 * UI-level permission helpers. These only hide/disable controls for a better
 * experience – the backend enforces every permission independently.
 */
export function usePermissions() {
  const auth = useAuthStore()
  return {
    can: (doctype: DocType, perm: PermType = 'read') => auth.can(doctype, perm),
    hasRole: (...roles: PgRole[]) => auth.hasRole(...roles),
    isAdmin: () => auth.isAdmin,
    canFinance: () => auth.can('PG Rent Invoice', 'read'),
  }
}
