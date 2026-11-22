import { ref } from 'vue'
import { toast } from 'vue-sonner'
import { ApiError } from '@/services/api'

/**
 * Run a server mutation with consistent toasts. Success is only reported after
 * the backend confirms; errors (including offline) are surfaced, never hidden.
 */
export function useMutation<A extends unknown[], R>(fn: (...args: A) => Promise<R>, opts: { success?: string | ((r: R) => string); silent?: boolean } = {}) {
  const pending = ref(false)
  const error = ref<string | null>(null)
  async function run(...args: A): Promise<R | undefined> {
    if (pending.value) return
    pending.value = true
    error.value = null
    try {
      const res = await fn(...args)
      const msg = typeof opts.success === 'function' ? opts.success(res) : opts.success ?? (res as any)?.message
      if (msg && !opts.silent) toast.success(msg)
      return res
    } catch (e) {
      const msg = e instanceof ApiError || e instanceof Error ? e.message : 'Something went wrong'
      error.value = msg
      if (!opts.silent) toast.error(msg)
      return undefined
    } finally {
      pending.value = false
    }
  }
  return { run, pending, error }
}
