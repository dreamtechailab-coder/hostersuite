import { computed, ref } from 'vue'

export function usePagination(initialSize = 20) {
  const page = ref(1)
  const pageSize = ref(initialSize)
  const total = ref(0)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const from = computed(() => (total.value ? (page.value - 1) * pageSize.value + 1 : 0))
  const to = computed(() => Math.min(total.value, page.value * pageSize.value))
  function setPage(p: number) {
    page.value = Math.min(Math.max(1, p), pageCount.value)
  }
  function reset() {
    page.value = 1
  }
  return { page, pageSize, total, pageCount, from, to, setPage, reset }
}
