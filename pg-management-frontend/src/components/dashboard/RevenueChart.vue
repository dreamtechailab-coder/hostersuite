<script setup lang="ts">
import { computed, ref } from 'vue'
import { Table2, LineChart as LineIcon } from 'lucide-vue-next'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { Button } from '@/components/ui/button'
import { baseOption, SERIES, type ChartTheme } from '@/lib/chart'
import { formatCurrency } from '@/utils/currency'
import { formatMonth } from '@/utils/date'

/** Monthly invoiced vs collected vs expenses – one currency axis, legend + crosshair tooltip. */
const props = withDefaults(
  defineProps<{ months: string[]; invoiced?: number[]; collected?: number[]; expenses?: number[]; height?: number }>(),
  { height: 280 },
)
const showTable = ref(false)
const series = computed(() =>
  [
    { key: 'invoiced', name: 'Invoiced', data: props.invoiced },
    { key: 'collected', name: 'Collected', data: props.collected },
    { key: 'expenses', name: 'Expenses', data: props.expenses },
  ].filter((s) => s.data) as { key: keyof typeof SERIES; name: string; data: number[] }[],
)
const hasData = computed(() => series.value.some((s) => s.data.some((v) => v)))

function build(t: ChartTheme) {
  return {
    ...baseOption(t),
    grid: { left: 8, right: 12, top: 40, bottom: 4, containLabel: true },
    legend: { top: 0, left: 0, icon: 'roundRect', itemWidth: 12, itemHeight: 4, textStyle: { color: t.text } },
    tooltip: {
      ...baseOption(t).tooltip,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: t.axis } },
      valueFormatter: (v: number) => formatCurrency(v),
    },
    xAxis: {
      type: 'category',
      data: props.months.map((m) => formatMonth(m, true)),
      axisLine: { lineStyle: { color: t.axis } },
      axisTick: { show: false },
      axisLabel: { color: t.text, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: t.grid } },
      axisLabel: { color: t.text, fontSize: 11, formatter: (v: number) => formatCurrency(v, { compact: true }) },
    },
    series: series.value.map((s) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      smooth: 0.25,
      symbol: 'circle',
      symbolSize: 8,
      showSymbol: false,
      lineStyle: { width: 2 },
      itemStyle: { color: t.palette[SERIES[s.key]], borderColor: t.surface, borderWidth: 2 },
      emphasis: { focus: 'series' },
    })),
  }
}
</script>

<template>
  <div>
    <div class="mb-1 flex justify-end">
      <Button variant="ghost" size="sm" :aria-pressed="showTable" @click="showTable = !showTable">
        <component :is="showTable ? LineIcon : Table2" />{{ showTable ? 'Chart' : 'Table' }}
      </Button>
    </div>
    <EmptyState v-if="!hasData" compact title="No financial activity yet" description="Invoices, payments and expenses will appear here." />
    <div v-else-if="showTable" class="max-h-80 overflow-auto">
      <table class="w-full text-sm">
        <thead class="sticky top-0 bg-card text-xs text-muted-foreground">
          <tr><th class="py-2 text-left font-medium">Month</th><th v-for="s in series" :key="s.key" class="py-2 text-right font-medium">{{ s.name }}</th></tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="(m, i) in months" :key="m">
            <td class="py-2">{{ formatMonth(m) }}</td>
            <td v-for="s in series" :key="s.key" class="tabular py-2 text-right">{{ formatCurrency(s.data[i]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <BaseChart v-else :build="build" :height="height" label="Monthly invoiced, collected and expenses trend" />
  </div>
</template>
