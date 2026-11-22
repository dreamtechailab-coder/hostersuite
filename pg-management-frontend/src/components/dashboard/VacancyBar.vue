<script setup lang="ts">
import { computed } from 'vue'
import { formatNumber } from '@/utils/currency'

/** Segmented bar of bed states with a legend (identity is never colour-only: every segment is labelled). */
const props = defineProps<{ occupied: number; reserved: number; vacant: number; maintenance: number }>()
const segments = computed(() => {
  const total = props.occupied + props.reserved + props.vacant + props.maintenance
  return [
    { key: 'Occupied', value: props.occupied, cls: 'bg-primary' },
    { key: 'Reserved', value: props.reserved, cls: 'bg-info' },
    { key: 'Vacant', value: props.vacant, cls: 'bg-success' },
    { key: 'Maintenance', value: props.maintenance, cls: 'bg-warning' },
  ].map((s) => ({ ...s, pct: total ? (s.value / total) * 100 : 0 }))
})
</script>

<template>
  <div>
    <div class="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-muted" role="img" :aria-label="segments.map((s) => `${s.key} ${s.value}`).join(', ')">
      <div v-for="s in segments.filter((x) => x.value)" :key="s.key" :class="[s.cls, 'h-full first:rounded-l-full last:rounded-r-full']" :style="{ width: `${s.pct}%` }" :title="`${s.key}: ${s.value}`" />
    </div>
    <ul class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <li v-for="s in segments" :key="s.key" class="flex items-start gap-2">
        <span :class="[s.cls, 'mt-1.5 size-2.5 shrink-0 rounded-sm']" />
        <div>
          <p class="text-xs text-muted-foreground">{{ s.key }}</p>
          <p class="tabular text-base font-semibold">{{ formatNumber(s.value) }} <span class="text-xs font-normal text-muted-foreground">{{ Math.round(s.pct) }}%</span></p>
        </div>
      </li>
    </ul>
  </div>
</template>
