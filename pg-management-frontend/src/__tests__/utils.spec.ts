import { describe, expect, it } from 'vitest'
import { formatCurrency, setCurrency } from '@/utils/currency'
import { addMonths, daysBetween, dueLabel, monthEnd, monthStart, parseDate, toISODate } from '@/utils/date'
import { aadhaar, email, mobile, positive, required, validate } from '@/utils/validation'
import { downloadCsv } from '@/utils/export'

describe('currency', () => {
  it('formats INR with Indian grouping', () => {
    setCurrency('INR')
    expect(formatCurrency(1250000)).toBe('₹12,50,000')
    expect(formatCurrency(99.5)).toBe('₹99.50')
  })
})

describe('date', () => {
  it('parses ISO dates as local dates (no UTC shift)', () => {
    expect(toISODate(parseDate('2026-03-01')!)).toBe('2026-03-01')
  })
  it('computes month bounds and offsets', () => {
    expect(monthStart('2026-02-14')).toBe('2026-02-01')
    expect(monthEnd('2026-02-14')).toBe('2026-02-28')
    expect(addMonths('2026-01-31', 1)).toBe('2026-02-01')
    expect(daysBetween('2026-01-01', '2026-01-11')).toBe(10)
  })
  it('labels due dates', () => {
    expect(dueLabel(toISODate())).toBe('Due today')
  })
})

describe('validation', () => {
  it('validates fields and returns the first error per field', () => {
    const errors = validate(
      { name: '', phone: '123', mail: 'x@y.com', amt: 0, id: '1234' },
      { name: [required('Name')], phone: [mobile], mail: [email], amt: [positive('Amount')], id: [aadhaar] },
    )
    expect(errors).toEqual({
      name: 'Name is required',
      phone: 'Enter a valid mobile number',
      amt: 'Amount must be greater than zero',
      id: 'Aadhaar must be 12 digits',
    })
  })
})

describe('csv export', () => {
  it('neutralises spreadsheet formulas', async () => {
    let blob: Blob | null = null
    const orig = URL.createObjectURL
    URL.createObjectURL = (b: Blob) => ((blob = b), 'blob:x')
    URL.revokeObjectURL = () => {}
    HTMLAnchorElement.prototype.click = () => {}
    downloadCsv('t.csv', [{ a: '=HYPERLINK("x")', b: 'ok, fine' }], [['A', 'a'], ['B', 'b']])
    URL.createObjectURL = orig
    const text = await new Promise<string>((resolve) => {
      const r = new FileReader()
      r.onload = () => resolve(String(r.result))
      r.readAsText(blob!)
    })
    expect(text).toContain(`"'=HYPERLINK(""x"")"`)
    expect(text).toContain('"ok, fine"')
  })
})
