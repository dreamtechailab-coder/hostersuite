import { reactive } from 'vue'

export interface ConfirmOptions {
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  destructive?: boolean
  /** ask for a free-text reason (e.g. cancellation) */
  withReason?: boolean
  reasonLabel?: string
}

const state = reactive({
  open: false,
  options: { title: '' } as ConfirmOptions,
  reason: '',
  resolve: null as null | ((v: { confirmed: boolean; reason?: string }) => void),
})

/** Promise-based global confirmation dialog (rendered once in App.vue). */
export function useConfirm() {
  function confirm(options: ConfirmOptions) {
    state.options = options
    state.reason = ''
    state.open = true
    return new Promise<{ confirmed: boolean; reason?: string }>((resolve) => {
      state.resolve = resolve
    })
  }
  return { confirm }
}
export function useConfirmState() {
  function close(confirmed: boolean) {
    state.open = false
    state.resolve?.({ confirmed, reason: state.reason || undefined })
    state.resolve = null
  }
  return { state, close }
}
