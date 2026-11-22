<script setup lang="ts">
import { ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ReportFilters from '@/components/reports/ReportFilters.vue'
import type { Preset } from '@/components/common/DateRangePicker.vue'
import { reportService } from '@/services/report.service'
import { useAsync } from '@/composables/useAsync'
import { usePropertyStore } from '@/stores/property'
import { baseOption, type ChartTheme } from '@/lib/chart'
import { downloadCsv } from '@/utils/export'
import { formatCurrency, formatPercent } from '@/utils/currency'
import { addMonths, formatMonth, monthEnd } from '@/utils/date'

const property = usePropertyStore()
const preset = ref<Preset>('last_12')
const range = ref({ from: addMonths(new Date(), -11), to: monthEnd() })
const { data, loading, error, run } = useAsync(() => reportService.occupancy({ property: property.filter, from_date: range.value.from, to_date: range.value.to }))
watch([() => property.filter, range], () => run(), { immediate: true, deep: true })
const sum = (k: 'beds' | 'occupied' | 'vacant') => (data.value?.by_property || []).reduce((a, r) => a + Number(r[k]), 0)
function build(t: ChartTheme) {
  const m = data.value?.movement || []
  return {
    ...baseOption(t),
    grid: { left: 8, right: 8, top: 36, bottom: 4, containLabel: true },
    legend: { top: 0, left: 0, icon: 'roundRect', itemWidth: 12, itemHeight: 4, textStyle: { color: t.text } },
    tooltip: { ...baseOption(t).tooltip, trigger: 'axis' },
    xAxis: { type: 'category', data: m.map((r) => formatMonth(r.m, true)), axisTick: { show: false }, axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.text, fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: t.grid } }, axisLabel: { color: t.text, fontSize: 11 } },
    series: [
      { name: 'Check-ins', type: 'bar', data: m.map((r) => Number(r.check_ins)), barMaxWidth: 16, barGap: '20%', itemStyle: { color: t.palette[0], borderRadius: [4, 4, 0, 0] } },
      { name: 'Check-outs', type: 'bar', data: m.map((r) => Number(r.check_outs)), barMaxWidth: 16, itemStyle: { color: t.palette[1], borderRadius: [4, 4, 0, 0] } },
    ],
  }
}
const exportCsv = () => downloadCsv('occupancy-report.csv', data.value?.by_property || [], [['Property', 'property_name'], ['Beds', 'beds'], ['Occupied', 'occupied'], ['Reserved', 'reserved'], ['Vacant', 'vacant'], ['Maintenance', 'maintenance'], ['Occupancy %', 'rate']])
</script>

<template>
  <div>
    <PageHeader title="Occupancy report" :description="property.label">
      <template #actions><ReportFilters v-model:range="range" v-model:preset="preset" :can-export="!!data?.by_property.length" @export="exportCsv" /></template>
    </PageHeader>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Occupancy" :value="formatPercent(sum('beds') ? (sum('occupied') * 100) / sum('beds') : 0)" :progress="sum('beds') ? (sum('occupied') * 100) / sum('beds') : 0" :loading="loading" />
        <StatCard label="Beds" :value="sum('beds')" :hint="`${sum('vacant')} vacant`" :loading="loading" />
        <StatCard label="Check-ins" :value="(data?.movement || []).reduce((a, r) => a + Number(r.check_ins), 0)" tone="success" hint="In selected period" :loading="loading" />
        <StatCard label="Average stay" :value="`${data?.average_stay_days ?? 0} days`" hint="Tenants who left in period" tone="info" :loading="loading" />
      </div>
      <Card class="mt-5">
        <CardHeader><div><CardTitle>Tenant movement</CardTitle><CardDescription>Check-ins vs check-outs per month</CardDescription></div></CardHeader>
        <CardContent>
          <EmptyState v-if="!data?.movement.length" compact title="No movement in this period" />
          <BaseChart v-else :build="build" :height="260" label="Monthly check-ins and check-outs" />
        </CardContent>
      </Card>
      <h2 class="mb-3 mt-6 font-semibold">By property</h2>
      <DataTable
        :columns="[
          { key: 'property_name', label: 'Property' },
          { key: 'beds', label: 'Beds', align: 'right' },
          { key: 'occupied', label: 'Occupied', align: 'right' },
          { key: 'reserved', label: 'Reserved', align: 'right' },
          { key: 'vacant', label: 'Vacant', align: 'right' },
          { key: 'maintenance', label: 'Maint.', align: 'right' },
          { key: 'rate', label: 'Occupancy', align: 'right' },
        ]"
        :rows="data?.by_property || []"
        :loading="loading"
        row-key="property"
      >
        <template #cell-rate="{ value }"><span class="tabular font-semibold">{{ formatPercent(value) }}</span></template>
      </DataTable>
      <h2 class="mb-3 mt-6 font-semibold">By sharing type</h2>
      <DataTable
        :columns="[
          { key: 'room_type', label: 'Type' },
          { key: 'beds', label: 'Beds', align: 'right' },
          { key: 'occupied', label: 'Occupied', align: 'right' },
          { key: 'avg_rent', label: 'Avg rent / bed', align: 'right' },
          { key: 'rate', label: 'Occupancy', align: 'right' },
        ]"
        :rows="data?.by_room_type || []"
        :loading="loading"
        row-key="room_type"
      >
        <template #cell-avg_rent="{ value }"><span class="tabular">{{ formatCurrency(Math.round(value)) }}</span></template>
        <template #cell-rate="{ value }"><span class="tabular font-semibold">{{ formatPercent(value) }}</span></template>
      </DataTable>
    </template>
  </div>
</template>
