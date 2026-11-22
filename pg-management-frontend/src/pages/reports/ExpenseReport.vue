<script setup lang="ts">
import { ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ExpenseChart from '@/components/dashboard/ExpenseChart.vue'
import ReportFilters from '@/components/reports/ReportFilters.vue'
import type { Preset } from '@/components/common/DateRangePicker.vue'
import { reportService } from '@/services/report.service'
import { useAsync } from '@/composables/useAsync'
import { usePropertyStore } from '@/stores/property'
import { baseOption, SERIES, type ChartTheme } from '@/lib/chart'
import { downloadCsv } from '@/utils/export'
import { formatCurrency } from '@/utils/currency'
import { addMonths, formatMonth, monthEnd } from '@/utils/date'

const property = usePropertyStore()
const preset = ref<Preset>('last_12')
const range = ref({ from: addMonths(new Date(), -11), to: monthEnd() })
const { data, loading, error, run } = useAsync(() => reportService.expense({ property: property.filter, from_date: range.value.from, to_date: range.value.to }))
watch([() => property.filter, range], () => run(), { immediate: true, deep: true })
function build(t: ChartTheme) {
  const m = data.value?.monthly || []
  return {
    ...baseOption(t),
    grid: { left: 8, right: 8, top: 12, bottom: 4, containLabel: true },
    tooltip: { ...baseOption(t).tooltip, trigger: 'axis', valueFormatter: (v: number) => formatCurrency(v) },
    xAxis: { type: 'category', data: m.map((r) => formatMonth(r.month, true)), axisTick: { show: false }, axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.text, fontSize: 11 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: t.grid } }, axisLabel: { color: t.text, fontSize: 11, formatter: (v: number) => formatCurrency(v, { compact: true }) } },
    series: [{ name: 'Expenses', type: 'bar', data: m.map((r) => Number(r.amount)), barMaxWidth: 28, itemStyle: { color: t.palette[SERIES.expenses], borderRadius: [4, 4, 0, 0] } }],
  }
}
const exportCsv = () => downloadCsv('expense-report.csv', data.value?.by_category || [], [['Category', 'name'], ['Entries', 'count'], ['Amount', 'value']])
</script>

<template>
  <div>
    <PageHeader title="Expense report" :description="property.label">
      <template #actions><ReportFilters v-model:range="range" v-model:preset="preset" :can-export="!!data?.by_category.length" @export="exportCsv" /></template>
    </PageHeader>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <StatCard label="Total expenses" :value="formatCurrency(data?.total)" tone="warning" :loading="loading" />
        <StatCard label="Monthly average" :value="formatCurrency(data?.monthly.length ? Math.round((data?.total || 0) / data.monthly.length) : 0)" :loading="loading" />
        <StatCard label="Largest category" :value="data?.by_category[0]?.name || '—'" :hint="data?.by_category[0] ? formatCurrency(data.by_category[0].value) : ''" :loading="loading" class="col-span-2 lg:col-span-1" />
      </div>
      <div class="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><div><CardTitle>Monthly spend</CardTitle></div></CardHeader>
          <CardContent>
            <EmptyState v-if="!data?.monthly.length" compact title="No expenses in this period" />
            <BaseChart v-else :build="build" :height="260" label="Monthly expenses" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><div><CardTitle>By category</CardTitle><CardDescription>Top categories</CardDescription></div></CardHeader>
          <CardContent><ExpenseChart :data="data?.by_category || []" /></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Top vendors</CardTitle></CardHeader>
          <CardContent>
            <EmptyState v-if="!data?.top_vendors.length" compact title="No vendor data" />
            <ul class="divide-y"><li v-for="v in data?.top_vendors || []" :key="v.name" class="flex justify-between py-2.5 text-sm"><span>{{ v.name }} <span class="text-muted-foreground">· {{ v.count }}</span></span><span class="tabular font-medium">{{ formatCurrency(v.value) }}</span></li></ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>By property</CardTitle></CardHeader>
          <CardContent>
            <ul class="divide-y"><li v-for="p in data?.by_property || []" :key="p.property" class="flex justify-between py-2.5 text-sm"><span>{{ p.property }}</span><span class="tabular font-medium">{{ formatCurrency(p.amount) }}</span></li></ul>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
