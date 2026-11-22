import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useAuthStore } from './auth'

const KEY = 'pg.selectedProperty' // UI preference only – not sensitive

/** Global property context. Empty string = "All properties". */
export const usePropertyStore = defineStore('property', () => {
  const auth = useAuthStore()
  let initial = ''
  try {
    initial = localStorage.getItem(KEY) || ''
  } catch {
    /* storage unavailable */
  }
  const selected = ref<string>(initial)

  const options = computed(() => auth.properties.filter((p) => p.is_active !== 0 || p.name === selected.value))
  const current = computed(() => auth.properties.find((p) => p.name === selected.value) || null)
  const label = computed(() => current.value?.property_name || 'All properties')
  /** Value to send as the `property` API parameter (undefined = all allowed). */
  const filter = computed(() => selected.value || undefined)

  // drop a selection the user no longer has access to
  watch(
    () => auth.properties,
    (list) => {
      if (selected.value && !list.some((p) => p.name === selected.value)) selected.value = ''
      if (!selected.value && list.length === 1) selected.value = list[0].name
    },
    { immediate: true },
  )
  watch(selected, (v) => {
    try {
      v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
  })

  function select(name: string) {
    selected.value = name
  }
  return { selected, options, current, label, filter, select }
})
