import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reportService, type DashboardData } from '@/services/report.service'
import { monthEnd, monthStart } from '@/utils/date'

export type RangePreset = 'month' | 'last_month' | 'quarter' | 'year' | 'custom'

/** Caches the last dashboard response per filter key to avoid refetching on navigation. */
export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref<DashboardData | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const preset = ref<RangePreset>('month')
  const range = ref({ from: monthStart(), to: monthEnd() })
  const cache = new Map<string, { at: number; data: DashboardData }>()
  let seq = 0

  async function load(property?: string, force = false) {
    const key = `${property || ''}|${range.value.from}|${range.value.to}`
    const hit = cache.get(key)
    if (!force && hit && Date.now() - hit.at < 60_000) {
      data.value = hit.data
      return
    }
    const id = ++seq
    loading.value = true
    error.value = null
    try {
      const res = await reportService.dashboard({ property, from_date: range.value.from, to_date: range.value.to })
      if (id !== seq) return
      data.value = res
      cache.set(key, { at: Date.now(), data: res })
    } catch (e) {
      if (id === seq) error.value = e as Error
    } finally {
      if (id === seq) loading.value = false
    }
  }

  function invalidate() {
    cache.clear()
  }
  return { data, loading, error, preset, range, load, invalidate }
})
