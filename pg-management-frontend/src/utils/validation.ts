/**
 * Lightweight form validation for UX only. The backend re-validates every
 * request – never rely on these checks for security.
 */
export type Rule = (value: any, form?: Record<string, any>) => string | true
export type Rules<T> = Partial<Record<keyof T, Rule[]>>

export const required =
  (label = 'This field'): Rule =>
  (v) =>
    (v !== null && v !== undefined && String(v).trim() !== '') || `${label} is required`

export const mobile: Rule = (v) => !v || /^\+?\d{10,15}$/.test(String(v).replace(/[\s-]/g, '')) || 'Enter a valid mobile number'
export const email: Rule = (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v)) || 'Enter a valid email address'
export const positive =
  (label = 'Amount'): Rule =>
  (v) =>
    v === '' || v === null || v === undefined || Number(v) > 0 || `${label} must be greater than zero`
export const nonNegative =
  (label = 'Value'): Rule =>
  (v) =>
    v === '' || v === null || v === undefined || Number(v) >= 0 || `${label} cannot be negative`
export const between =
  (min: number, max: number, label = 'Value'): Rule =>
  (v) =>
    v === '' || v == null || (Number(v) >= min && Number(v) <= max) || `${label} must be between ${min} and ${max}`
export const aadhaar: Rule = (v) => !v || /^\d{12}$/.test(String(v).replace(/\s/g, '')) || 'Aadhaar must be 12 digits'
export const pan: Rule = (v) => !v || /^[A-Z]{5}\d{4}[A-Z]$/.test(String(v).toUpperCase()) || 'Invalid PAN format'
export const minLength =
  (n: number, label = 'Value'): Rule =>
  (v) =>
    !v || String(v).length >= n || `${label} must be at least ${n} characters`

export function validate<T extends Record<string, any>>(form: T, rules: Rules<T>): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const key in rules) {
    for (const rule of rules[key] || []) {
      const res = rule(form[key], form)
      if (res !== true) {
        errors[key] = res
        break
      }
    }
  }
  return errors
}

/** Generates an idempotency key for financial mutations. */
export function requestId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}
