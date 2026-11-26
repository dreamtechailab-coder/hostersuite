<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CalendarRange } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { addMonths, formatDate, monthEnd, monthStart, toISODate } from '@/utils/date'

export type Preset = 'month' | 'last_month' | 'quarter' | 'year' | 'last_12' | 'custom'
const model = defineModel<{ from: string; to: string }>({ required: true })
const preset = defineModel<Preset>('preset', { default: 'month' })
const props = withDefaults(defineProps<{ presets?: Preset[] }>(), {
  presets: () => ['month', 'last_month', 'quarter', 'year', 'last_12', 'custom'],
})

const LABELS: Record<Preset, string> = {
  month: 'This month',
  last_month: 'Last month',
  quarter: 'This quarter',
  year: 'This year',
  last_12: 'Last 12 months',
  custom: 'Custom range',
}
function rangeFor(p: Preset) {
  const now = new Date()
  switch (p) {
    case 'month':
      return { from: monthStart(), to: monthEnd() }
    case 'last_month': {
      const s = addMonths(now, -1)
      return { from: s, to: monthEnd(s) }
    }
    case 'quarter': {
      const q = Math.floor(now.getMonth() / 3) * 3
      return { from: toISODate(new Date(now.getFullYear(), q, 1)), to: toISODate(new Date(now.getFullYear(), q + 3, 0)) }
    }
    case 'year':
      return { from: `${now.getFullYear()}-01-01`, to: `${now.getFullYear()}-12-31` }
    case 'last_12':
      return { from: addMonths(now, -11), to: monthEnd() }
    default:
      return model.value
  }
}
const open = ref(false)
const draft = ref({ ...model.value })
watch(model, (v) => (draft.value = { ...v }))

function choose(p: Preset) {
  preset.value = p
  if (p !== 'custom') {
    model.value = rangeFor(p)
    open.value = false
  }
}
function applyCustom() {
  if (draft.value.from && draft.value.to && draft.value.from <= draft.value.to) {
    model.value = { ...draft.value }
    open.value = false
  }
}
const label = computed(() =>
  preset.value === 'custom'
    ? `${formatDate(model.value.from, { day: 'numeric', month: 'short' })} – ${formatDate(model.value.to, { day: 'numeric', month: 'short', year: 'numeric' })}`
    : LABELS[preset.value],
)
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button variant="outline" class="justify-start">
        <CalendarRange />
        <span class="truncate">{{ label }}</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent align="end" class="w-[min(18rem,calc(100vw-2rem))] p-2">
      <div class="grid gap-0.5">
        <button
          v-for="p in props.presets"
          :key="p"
          type="button"
          :class="['rounded-md px-3 py-2 text-left text-sm hover:bg-accent', preset === p && 'bg-accent font-medium text-accent-foreground']"
          @click="choose(p)"
        >
          {{ LABELS[p] }}
        </button>
      </div>
      <div v-if="preset === 'custom'" class="mt-2 space-y-2 border-t p-2 pt-3">
        <label class="block text-xs text-muted-foreground">From
          <input v-model="draft.from" type="date" class="mt-1 h-10 w-full rounded-md border bg-card px-2 text-base md:h-9 md:text-sm" />
        </label>
        <label class="block text-xs text-muted-foreground">To
          <input v-model="draft.to" type="date" :min="draft.from" class="mt-1 h-10 w-full rounded-md border bg-card px-2 text-base md:h-9 md:text-sm" />
        </label>
        <Button size="sm" class="w-full" :disabled="!draft.from || !draft.to || draft.from > draft.to" @click="applyCustom">Apply</Button>
      </div>
    </PopoverContent>
  </Popover>
</template>
