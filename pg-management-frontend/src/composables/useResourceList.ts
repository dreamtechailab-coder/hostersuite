import { ref, shallowRef, watch, type Ref } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { resource } from '@/services/resource.service'
import { usePropertyStore } from '@/stores/property'
import { usePagination } from './usePagination'
import type { DocType, Filters } from '@/types'

interface Options {
  filters?: Ref<Filters> | (() => Filters)
  orderBy?: Ref<string> | string
  pageSize?: number
  /** add the globally selected property as a filter (default true) */
  scoped?: boolean
  immediate?: boolean
}

/** Paginated, searchable, server-filtered list for an allow-listed DocType. */
export function useResourceList<T>(doctype: DocType, opts: Options = {}) {
  const propertyStore = usePropertyStore()
  const rows = shallowRef<T[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const search = ref('')
  const { page, pageSize, total, pageCount, from, to, setPage, reset } = usePagination(opts.pageSize || 20)
  const orderBy = ref(typeof opts.orderBy === 'string' ? opts.orderBy : opts.orderBy?.value || '')
  let seq = 0

  function currentFilters(): Filters {
    const f = typeof opts.filters === 'function' ? opts.filters() : opts.filters?.value || {}
    const out: Filters = { ...f }
    if (opts.scoped !== false && propertyStore.filter && !('property' in out)) out.property = propertyStore.filter
    return out
  }

  async function load() {
    const id = ++seq
    loading.value = true
    error.value = null
    try {
      const res = await resource.list<T>(doctype, {
        filters: currentFilters(),
        search: search.value || undefined,
        page: page.value,
        page_size: pageSize.value,
        order_by: orderBy.value || undefined,
      })
      if (id !== seq) return
      rows.value = res.data
      total.value = res.total
    } catch (e) {
      if (id === seq) error.value = e as Error
    } finally {
      if (id === seq) loading.value = false
    }
  }

  watch(page, load)
  watchDebounced(search, () => (page.value === 1 ? load() : reset()), { debounce: 300 })
  watch(
    [() => JSON.stringify(currentFilters()), orderBy, pageSize],
    () => (page.value === 1 ? load() : reset()),
  )
  if (opts.immediate !== false) load()

  return { rows, loading, error, search, page, pageSize, total, pageCount, from, to, setPage, orderBy, reload: load }
}
