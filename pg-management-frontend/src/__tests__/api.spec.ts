import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, parseFrappeError, setCsrfToken, onSessionExpired } from '@/services/api'

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockImplementation(async () => new Response(JSON.stringify(body), { status }))
  vi.stubGlobal('fetch', fn)
  return fn
}
afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('unwraps Frappe message envelope on GET with query params', async () => {
    const f = mockFetch(200, { message: { data: [1] } })
    const res = await api.pgGet<{ data: number[] }>('resource.get_list', { doctype: 'PG Room', filters: { a: 1 } })
    expect(res.data).toEqual([1])
    const url = f.mock.calls[0][0] as string
    expect(url).toContain('/api/method/pg_managment_system.api.resource.get_list?')
    expect(url).toContain('filters=%7B%22a%22%3A1%7D')
  })

  it('sends the CSRF token on POST and never on GET', async () => {
    setCsrfToken('tok123')
    const f = mockFetch(200, { message: 'ok' })
    await api.post('x.y', { a: 1 })
    expect((f.mock.calls[0][1] as RequestInit).headers).toMatchObject({ 'X-Frappe-CSRF-Token': 'tok123' })
    await api.get('x.y')
    expect((f.mock.calls[1][1] as RequestInit).headers).not.toHaveProperty('X-Frappe-CSRF-Token')
  })

  it('parses _server_messages into a readable error', () => {
    const err = parseFrappeError(
      { exc_type: 'ValidationError', _server_messages: JSON.stringify([JSON.stringify({ message: 'Bed is <b>occupied</b>' })]) },
      417,
    )
    expect(err).toBeInstanceOf(ApiError)
    expect(err.message).toBe('Bed is occupied')
    expect(err.type).toBe('ValidationError')
  })

  it('refuses writes while offline instead of pretending success', async () => {
    const f = mockFetch(200, { message: 'ok' })
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    await expect(api.post('pg.collect', {})).rejects.toMatchObject({ offline: true })
    expect(f).not.toHaveBeenCalled()
    vi.restoreAllMocks()
  })

  it('notifies listeners when the session expires', async () => {
    mockFetch(401, { exc_type: 'SessionExpired' })
    const spy = vi.fn()
    const off = onSessionExpired(spy)
    await expect(api.get('x')).rejects.toBeInstanceOf(ApiError)
    expect(spy).toHaveBeenCalled()
    off()
  })
})
