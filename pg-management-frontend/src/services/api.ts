/**
 * Thin, typed client for Frappe whitelisted methods.
 *
 * - Uses Frappe's cookie session (same-origin) – no tokens in localStorage.
 * - Sends the CSRF token (kept in memory only) on every unsafe request.
 * - Normalises Frappe errors into ApiError with a human readable message.
 * - Never queues or replays writes while offline: a mutation either reaches the
 *   server and is confirmed, or it fails loudly.
 */

export const PG = 'pg_managment_system.api'

let csrfToken = ''
export function setCsrfToken(token: string | undefined) {
  csrfToken = token || ''
}

type Listener = () => void
const sessionExpiredListeners = new Set<Listener>()
export function onSessionExpired(fn: Listener) {
  sessionExpiredListeners.add(fn)
  return () => sessionExpiredListeners.delete(fn)
}

export class ApiError extends Error {
  status: number
  type?: string
  offline: boolean
  constructor(message: string, status = 0, type?: string, offline = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.type = type
    this.offline = offline
  }
  get isPermission() {
    return this.status === 403 || this.type === 'PermissionError'
  }
  get isNotFound() {
    return this.status === 404 || this.type === 'DoesNotExistError'
  }
}

function stripHtml(s: string) {
  const div = typeof document !== 'undefined' ? document.createElement('div') : null
  if (!div) return s.replace(/<[^>]+>/g, '')
  div.innerHTML = s
  return div.textContent || div.innerText || ''
}

export function parseFrappeError(body: any, status: number): ApiError {
  let message = ''
  try {
    if (body?._server_messages) {
      const msgs = JSON.parse(body._server_messages) as string[]
      message = msgs
        .map((m) => {
          try {
            return JSON.parse(m).message
          } catch {
            return m
          }
        })
        .filter(Boolean)
        .join('\n')
    }
  } catch {
    /* ignore malformed server messages */
  }
  if (!message && typeof body?.message === 'string') message = body.message
  if (!message && body?.exception) message = String(body.exception).split(':').slice(1).join(':').trim()
  if (!message) {
    message =
      status === 403
        ? 'You do not have permission to do this.'
        : status === 404
          ? 'The requested record was not found.'
          : status >= 500
            ? 'The server ran into a problem. Please try again.'
            : 'Something went wrong.'
  }
  return new ApiError(stripHtml(message), status, body?.exc_type)
}

function toQuery(params?: Record<string, unknown>) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null || v === '') continue
    qs.append(k, typeof v === 'object' ? JSON.stringify(v) : String(v))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

async function request<T>(method: 'GET' | 'POST', path: string, params?: Record<string, unknown>, retried = false): Promise<T> {
  if (method === 'POST' && typeof navigator !== 'undefined' && navigator.onLine === false) {
    throw new ApiError('You are offline. Changes cannot be saved until you reconnect.', 0, 'Offline', true)
  }
  const url = `/api/method/${path}${method === 'GET' ? toQuery(params) : ''}`
  const headers: Record<string, string> = { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
  let body: string | undefined
  if (method === 'POST') {
    headers['Content-Type'] = 'application/json'
    if (csrfToken) headers['X-Frappe-CSRF-Token'] = csrfToken
    body = JSON.stringify(params || {})
  }
  let res: Response
  try {
    res = await fetch(url, { method, headers, body, credentials: 'same-origin', cache: 'no-store' })
  } catch {
    const offline = typeof navigator !== 'undefined' && navigator.onLine === false
    throw new ApiError(
      offline ? 'You are offline. Check your connection and try again.' : 'Could not reach the server. Please try again.',
      0,
      'NetworkError',
      true,
    )
  }
  let json: any = null
  const text = await res.text()
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    json = null
  }
  if (!res.ok) {
    const err = parseFrappeError(json, res.status)
    if (err.type === 'CSRFTokenError' && !retried) {
      // token rotated (e.g. after re-login in another tab) – refresh and retry once
      const s = await request<{ data: { csrf_token?: string } }>('GET', `${PG}.session.get_session`)
      setCsrfToken(s.data?.csrf_token)
      return request<T>(method, path, params, true)
    }
    if (res.status === 401 || err.type === 'SessionExpired' || (res.status === 403 && err.type === 'PermissionError' && /login/i.test(err.message))) {
      sessionExpiredListeners.forEach((fn) => fn())
    }
    throw err
  }
  return (json?.message ?? json) as T
}

export const api = {
  get: <T>(method: string, params?: Record<string, unknown>) => request<T>('GET', method, params),
  post: <T>(method: string, params?: Record<string, unknown>) => request<T>('POST', method, params),
  /** Call a method of this app: api.pg('rent.get_invoice', {...}) */
  pgGet: <T>(method: string, params?: Record<string, unknown>) => request<T>('GET', `${PG}.${method}`, params),
  pgPost: <T>(method: string, params?: Record<string, unknown>) => request<T>('POST', `${PG}.${method}`, params),
}

/** Upload a file through Frappe (private by default, attached to a document). */
export async function uploadFile(
  file: File,
  opts: { doctype?: string; docname?: string; fieldname?: string; isPrivate?: boolean } = {},
): Promise<{ file_url: string; name: string; file_name: string }> {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    throw new ApiError('You are offline. Files cannot be uploaded.', 0, 'Offline', true)
  }
  const form = new FormData()
  form.append('file', file, file.name)
  form.append('is_private', opts.isPrivate === false ? '0' : '1')
  if (opts.doctype) form.append('doctype', opts.doctype)
  if (opts.docname) form.append('docname', opts.docname)
  if (opts.fieldname) form.append('fieldname', opts.fieldname)
  const res = await fetch('/api/method/upload_file', {
    method: 'POST',
    body: form,
    credentials: 'same-origin',
    headers: { Accept: 'application/json', 'X-Frappe-CSRF-Token': csrfToken },
  })
  const json = await res.json().catch(() => null)
  if (!res.ok) throw parseFrappeError(json, res.status)
  return json.message
}
