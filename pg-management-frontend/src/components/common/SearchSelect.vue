<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { Check, ChevronsUpDown, Loader2, X } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { resource } from '@/services/resource.service'
import { cn } from '@/lib/utils'
import type { DocType, Filters, Option } from '@/types'

/** Async, searchable link field backed by resource.get_options. */
const props = withDefaults(
  defineProps<{
    doctype?: DocType
    options?: Option[]
    filters?: Filters
    placeholder?: string
    disabled?: boolean
    invalid?: boolean
    id?: string
    initialLabel?: string
    clearable?: boolean
  }>(),
  { placeholder: 'Select…', clearable: true },
)
const model = defineModel<string | null | undefined>()
const emit = defineEmits<{ change: [option: Option | null] }>()

const open = ref(false)
const query = ref('')
const loading = ref(false)
const remote = ref<Option[]>([])
const selectedLabel = ref(props.initialLabel || '')
const items = computed(() => {
  if (props.options) {
    const q = query.value.toLowerCase()
    return props.options.filter((o) => !q || o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q))
  }
  return remote.value
})

async function fetchOptions() {
  if (!props.doctype) return
  loading.value = true
  try {
    remote.value = await resource.options(props.doctype, { filters: props.filters, search: query.value || undefined, limit: 30 })
  } catch {
    remote.value = []
  } finally {
    loading.value = false
  }
}
watchDebounced(query, fetchOptions, { debounce: 250 })
watch(open, (o) => o && fetchOptions())
watch(
  () => JSON.stringify(props.filters),
  () => (remote.value = []),
)
watch(
  () => [model.value, props.options, props.initialLabel] as const,
  ([v]) => {
    if (!v) return (selectedLabel.value = '')
    const found = (props.options || remote.value).find((o) => o.value === v)
    if (found) selectedLabel.value = found.label
    else if (props.initialLabel) selectedLabel.value = props.initialLabel
    else if (props.doctype && !selectedLabel.value)
      resource.options(props.doctype, { filters: { name: v }, limit: 1 }).then((r) => (selectedLabel.value = r[0]?.label || v))
  },
  { immediate: true },
)

function pick(o: Option | null) {
  model.value = o?.value ?? ''
  selectedLabel.value = o?.label ?? ''
  emit('change', o)
  open.value = false
  query.value = ''
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child :disabled="disabled">
      <button
        :id="id"
        type="button"
        role="combobox"
        :aria-expanded="open"
        :aria-invalid="invalid || undefined"
        :disabled="disabled"
        :class="
          cn(
            'flex h-10 w-full items-center gap-2 rounded-lg border border-input bg-card px-3 text-left text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/25 disabled:opacity-50 md:text-sm',
            invalid && 'border-destructive',
          )
        "
      >
        <span :class="['min-w-0 flex-1 truncate', !model && 'text-muted-foreground/70']">{{ model ? selectedLabel || model : placeholder }}</span>
        <X v-if="model && clearable && !disabled" class="size-4 text-muted-foreground hover:text-foreground" @click.stop="pick(null)" />
        <ChevronsUpDown class="size-4 shrink-0 text-muted-foreground" />
      </button>
    </PopoverTrigger>
    <PopoverContent class="w-[var(--reka-popover-trigger-width)] min-w-64 p-0" align="start">
      <div class="border-b p-2">
        <input
          v-model="query"
          type="search"
          class="h-9 w-full rounded-md bg-muted/50 px-3 text-base outline-none md:text-sm"
          placeholder="Type to search…"
          aria-label="Search options"
          autofocus
        />
      </div>
      <ul class="max-h-64 overflow-y-auto p-1" role="listbox">
        <li v-if="loading" class="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground"><Loader2 class="size-4 animate-spin" />Loading…</li>
        <li v-else-if="!items.length" class="py-6 text-center text-sm text-muted-foreground">No matches</li>
        <li v-for="o in loading ? [] : items" :key="o.value">
          <button
            type="button"
            role="option"
            :aria-selected="o.value === model"
            class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-accent"
            @click="pick(o)"
          >
            <Check :class="['size-4 shrink-0', o.value === model ? 'text-primary' : 'opacity-0']" />
            <span class="min-w-0 flex-1 truncate">{{ o.label }}</span>
            <span v-if="o.hint" class="text-xs text-muted-foreground">{{ o.hint }}</span>
          </button>
        </li>
      </ul>
    </PopoverContent>
  </Popover>
</template>
