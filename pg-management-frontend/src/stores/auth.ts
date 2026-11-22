import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authService } from '@/services/auth.service'
import { setCsrfToken } from '@/services/api'
import { setCurrency } from '@/utils/currency'
import type { DocType, PermType, PgRole, SessionInfo } from '@/types'

/**
 * Session state lives in memory only (cookie-based Frappe session). Nothing
 * sensitive is persisted to localStorage.
 */
export const useAuthStore = defineStore('auth', () => {
  const session = ref<SessionInfo | null>(null)
  const initialized = ref(false)
  let initPromise: Promise<void> | null = null

  const isLoggedIn = computed(() => !!session.value?.user)
  const user = computed(() => session.value)
  const roles = computed(() => session.value?.roles || [])
  const isAdmin = computed(() => !!session.value?.is_admin)
  const properties = computed(() => session.value?.properties || [])
  const settings = computed(() => session.value?.settings)

  function apply(s: SessionInfo | null) {
    session.value = s && s.user ? s : null
    setCsrfToken(s?.csrf_token)
    setCurrency(s?.settings?.currency)
  }

  async function refresh() {
    try {
      apply(await authService.getSession())
    } catch {
      apply(null)
    }
  }

  function init() {
    if (!initPromise) {
      initPromise = refresh().finally(() => {
        initialized.value = true
      })
    }
    return initPromise
  }

  async function login(username: string, password: string) {
    await authService.login(username.trim(), password)
    await refresh()
    if (!session.value) throw new Error('Login succeeded but the session could not be loaded.')
  }

  async function logout() {
    try {
      await authService.logout()
    } finally {
      clearSession()
    }
  }

  function clearSession() {
    apply(null)
  }

  function can(doctype: DocType, perm: PermType = 'read') {
    return !!session.value?.can?.[doctype]?.[perm]
  }
  function hasRole(...r: PgRole[]) {
    return isAdmin.value || r.some((x) => roles.value.includes(x))
  }

  return { session, initialized, isLoggedIn, user, roles, isAdmin, properties, settings, init, refresh, login, logout, clearSession, can, hasRole }
})
