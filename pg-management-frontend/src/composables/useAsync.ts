import { ref, shallowRef } from 'vue'

/** Wrap an async loader with loading/error state and stale-response protection. */
export function useAsync<T, A extends unknown[] = []>(fn: (...args: A) => Promise<T>, opts: { immediate?: boolean } = {}) {
  const data = shallowRef<T | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  let seq = 0
  async function run(...args: A) {
    const id = ++seq
    loading.value = true
    error.value = null
    try {
      const res = await fn(...args)
      if (id === seq) data.value = res
      return res
    } catch (e) {
      if (id === seq) error.value = e as Error
    } finally {
      if (id === seq) loading.value = false
    }
  }
  if (opts.immediate) (run as () => Promise<T | undefined>)()
  return { data, loading, error, run }
}
