let currentCurrency = 'INR'
const formatters = new Map<string, Intl.NumberFormat>()

export function setCurrency(code?: string) {
  if (code) currentCurrency = code
}
export function getCurrency() {
  return currentCurrency
}

function formatter(compact: boolean, decimals: number) {
  const key = `${currentCurrency}|${compact}|${decimals}`
  if (!formatters.has(key)) {
    formatters.set(
      key,
      new Intl.NumberFormat(currentCurrency === 'INR' ? 'en-IN' : undefined, {
        style: 'currency',
        currency: currentCurrency,
        notation: compact ? 'compact' : 'standard',
        maximumFractionDigits: decimals,
        minimumFractionDigits: compact ? 0 : decimals,
      }),
    )
  }
  return formatters.get(key)!
}

/** ₹12,500 (whole units shown without decimals unless needed) */
export function formatCurrency(value: number | string | null | undefined, opts: { compact?: boolean; decimals?: number } = {}) {
  const n = Number(value || 0)
  const decimals = opts.decimals ?? (Number.isInteger(n) ? 0 : 2)
  return formatter(!!opts.compact, decimals).format(n)
}

export function formatNumber(value: number | string | null | undefined, decimals = 0) {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: decimals }).format(Number(value || 0))
}

export function formatPercent(value: number | null | undefined, decimals = 1) {
  return `${Number(value || 0).toFixed(decimals).replace(/\.0+$/, '')}%`
}
