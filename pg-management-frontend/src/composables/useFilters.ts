import { computed, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Reactive filter object synced to the URL query string, so filtered views
 * are shareable and survive refresh / back navigation.
 */
export function useFilters<T extends Record<string, string>>(defaults: T, opts: { sync?: boolean } = { sync: true }) {
  const route = useRoute()
  const router = useRouter()
  const initial = { ...defaults } as T
  if (opts.sync) {
    for (const key of Object.keys(defaults)) {
      const q = route.query[key]
      if (typeof q === 'string') (initial as Record<string, string>)[key] = q
    }
  }
  const filters = reactive({ ...initial }) as T

  const activeCount = computed(() => Object.keys(defaults).filter((k) => filters[k] !== defaults[k] && filters[k] !== '').length)

  if (opts.sync) {
    watch(
      () => ({ ...filters }),
      (val) => {
        const query = { ...route.query }
        for (const [k, v] of Object.entries(val)) {
          if (v && v !== defaults[k]) query[k] = v as string
          else delete query[k]
        }
        router.replace({ query }).catch(() => {})
      },
    )
  }

  function reset() {
    Object.assign(filters, defaults)
  }
  return { filters, activeCount, reset }
}
