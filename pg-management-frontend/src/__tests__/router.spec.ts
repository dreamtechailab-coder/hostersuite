import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { SessionInfo } from '@/types'

vi.mock('virtual:pwa-register/vue', () => ({ useRegisterSW: () => ({}) }))

async function freshRouter(session: SessionInfo) {
  vi.resetModules()
  vi.doMock('@/services/auth.service', () => ({ authService: { getSession: vi.fn().mockResolvedValue(session) } }))
  setActivePinia(createPinia())
  const { router } = await import('@/router')
  return router
}

describe('route guards (usability layer)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    window.scrollTo = () => {}
  })

  it('redirects guests to login with a redirect back', async () => {
    const router = await freshRouter({ user: null })
    await router.push('/tenants')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/tenants')
  })

  it('blocks routes the role cannot read', async () => {
    const router = await freshRouter({
      user: 'staff@x.com',
      roles: ['PG Staff'],
      can: { 'PG Tenant': { read: true }, 'PG Payment': { read: false } } as any,
    })
    await router.push('/payments')
    expect(router.currentRoute.value.name).toBe('forbidden')
    await router.push('/settings/users')
    expect(router.currentRoute.value.name).toBe('forbidden')
  })
})
