const pad = (n: number) => String(n).padStart(2, '0')

/** Parse "YYYY-MM-DD" (or datetime) as a LOCAL date – avoids UTC off-by-one. */
export function parseDate(value?: string | Date | null): Date | null {
  if (!value) return null
  if (value instanceof Date) return value
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(value)
  if (!m) return new Date(value)
  return new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0), +(m[6] || 0))
}

export function toISODate(d: Date = new Date()) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
export const today = () => toISODate()

export function addDays(value: string | Date, days: number) {
  const d = new Date(parseDate(value)!)
  d.setDate(d.getDate() + days)
  return toISODate(d)
}

export function monthStart(value: string | Date = new Date()) {
  const d = parseDate(value)!
  return toISODate(new Date(d.getFullYear(), d.getMonth(), 1))
}
export function monthEnd(value: string | Date = new Date()) {
  const d = parseDate(value)!
  return toISODate(new Date(d.getFullYear(), d.getMonth() + 1, 0))
}
export function addMonths(value: string | Date, months: number) {
  const d = parseDate(value)!
  return toISODate(new Date(d.getFullYear(), d.getMonth() + months, 1))
}

export function formatDate(value?: string | Date | null, opts: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short', year: 'numeric' }) {
  const d = parseDate(value)
  return d ? d.toLocaleDateString('en-IN', opts) : '—'
}
export function formatDateTime(value?: string | null) {
  const d = parseDate(value)
  return d ? d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: 'numeric', minute: '2-digit' }) : '—'
}
/** "2026-03" or a date -> "Mar 2026" */
export function formatMonth(value?: string | null, short = false) {
  if (!value) return '—'
  const d = parseDate(value.length === 7 ? `${value}-01` : value)
  return d ? d.toLocaleDateString('en-IN', { month: short ? 'short' : 'long', year: short ? '2-digit' : 'numeric' }) : '—'
}

export function daysBetween(a: string | Date, b: string | Date) {
  const ms = parseDate(b)!.setHours(0, 0, 0, 0) - parseDate(a)!.setHours(0, 0, 0, 0)
  return Math.round(ms / 86400000)
}

export function relativeTime(value?: string | null) {
  const d = parseDate(value)
  if (!d) return ''
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 7 * 86400) return `${Math.floor(diff / 86400)}d ago`
  return formatDate(d, { day: 'numeric', month: 'short' })
}

/** Due label relative to today: "Due in 3 days", "Overdue by 5 days", "Due today" */
export function dueLabel(due?: string | null) {
  if (!due) return ''
  const n = daysBetween(today(), due)
  if (n === 0) return 'Due today'
  if (n > 0) return `Due in ${n} day${n > 1 ? 's' : ''}`
  return `Overdue by ${-n} day${n < -1 ? 's' : ''}`
}
