/** Client-side CSV export of rows already loaded (respects server permissions). */
export function downloadCsv(filename: string, rows: Record<string, any>[], columns: [label: string, key: string][]) {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? '' : String(v)
    // neutralise spreadsheet formula injection
    const safe = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s
    return /[",\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe
  }
  const lines = [columns.map(([l]) => esc(l)).join(','), ...rows.map((r) => columns.map(([, k]) => esc(r[k])).join(','))]
  const blob = new Blob(['﻿' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
