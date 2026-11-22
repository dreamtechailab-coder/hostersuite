<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { baseOption, SERIES, type ChartTheme } from '@/lib/chart'
import { formatCurrency } from '@/utils/currency'
import type { NamedValue } from '@/types'

/**
 * Expense magnitude by category – a single-hue horizontal bar (sorted), which
 * reads better than a many-slice pie. Beyond 7 categories folds into "Other".
 */
const props = withDefaults(defineProps<{ data: NamedValue[]; max?: number }>(), { max: 7 })
const rows = computed(() => {
  const sorted = [...props.data].sort((a, b) => b.value - a.value)
  if (sorted.length <= props.max) return sorted
  const other = sorted.slice(props.max).reduce((s, r) => s + Number(r.value), 0)
  return [...sorted.slice(0, props.max), { name: 'Other', value: other }]
})
const height = computed(() => Math.max(140, rows.value.length * 36 + 20))
function build(t: ChartTheme) {
  const r = [...rows.value].reverse()
  return {
    ...baseOption(t),
    grid: { left: 4, right: 70, top: 4, bottom: 4, containLabel: true },
    tooltip: { ...baseOption(t).tooltip, trigger: 'item', valueFormatter: (v: number) => formatCurrency(v) },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: r.map((x) => x.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: t.text, fontSize: 12 } },
    series: [
      {
        type: 'bar',
        name: 'Expenses',
        data: r.map((x) => Number(x.value)),
        barWidth: 14,
        itemStyle: { color: t.palette[SERIES.expenses], borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', color: t.text, fontSize: 11, formatter: (p: { value: number }) => formatCurrency(p.value, { compact: true }) },
      },
    ],
  }
}
</script>

<template>
  <EmptyState v-if="!rows.length" compact title="No expenses in this period" />
  <BaseChart v-else :build="build" :height="height" label="Expenses by category" />
</template>
