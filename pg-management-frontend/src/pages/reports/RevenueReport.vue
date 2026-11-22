<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import RevenueChart from '@/components/dashboard/RevenueChart.vue'
import ReportFilters from '@/components/reports/ReportFilters.vue'
import type { Preset } from '@/components/common/DateRangePicker.vue'
import { reportService } from '@/services/report.service'
import { useAsync } from '@/composables/useAsync'
import { usePropertyStore } from '@/stores/property'
import { downloadCsv } from '@/utils/export'
import { formatCurrency, formatPercent } from '@/utils/currency'
import { addMonths, formatMonth, monthEnd } from '@/utils/date'

const property = usePropertyStore()
const preset = ref<Preset>('last_12')
const range = ref({ from: addMonths(new Date(), -11), to: monthEnd() })
const { data, loading, error, run } = useAsync(() => reportService.revenue({ property: property.filter, from_date: range.value.from, to_date: range.value.to }))
watch([() => property.filter, range], () => run(), { immediate: true, deep: true })
const monthly = computed(() => {
  const map = new Map<string, { month: string; invoiced: number; collected: number; outstanding: number; invoices: number }>()
  for (const r of data.value?.monthly || []) {
    const m = map.get(r.month) || { month: r.month, invoiced: 0, collected: 0, outstanding: 0, invoices: 0 }
    m.invoiced += Number(r.invoiced)
    m.collected += Number(r.collected)
    m.outstanding += Number(r.outstanding)
    m.invoices += Number(r.invoices)
    map.set(r.month, m)
  }
  return [...map.values()]
})
const rate = computed(() => (data.value?.totals.invoiced ? (data.value.totals.collected * 100) / data.value.totals.invoiced : 0))
const exportCsv = () => downloadCsv('revenue-report.csv', data.value?.monthly || [], [['Month', 'month'], ['Property', 'property'], ['Invoices', 'invoices'], ['Invoiced', 'invoiced'], ['Collected', 'collected'], ['Outstanding', 'outstanding']])
</script>

<template>
  <div>
    <PageHeader title="Revenue report" :description="property.label">
      <template #actions><ReportFilters v-model:range="range" v-model:preset="preset" :can-export="!!data?.monthly.length" @export="exportCsv" /></template>
    </PageHeader>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Invoiced" :value="formatCurrency(data?.totals.invoiced)" :loading="loading" />
        <StatCard label="Collected (against these invoices)" :value="formatCurrency(data?.totals.collected)" tone="success" :loading="loading" />
        <StatCard label="Collection rate" :value="formatPercent(rate)" :progress="rate" tone="success" :loading="loading" />
        <StatCard label="Still outstanding" :value="formatCurrency(data?.totals.outstanding)" tone="danger" :loading="loading" />
      </div>
      <Card class="mt-5">
        <CardHeader><CardTitle>Invoiced vs collected</CardTitle></CardHeader>
        <CardContent><RevenueChart :months="monthly.map((m) => m.month)" :invoiced="monthly.map((m) => m.invoiced)" :collected="monthly.map((m) => m.collected)" /></CardContent>
      </Card>
      <div class="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Revenue by charge type</CardTitle></CardHeader>
          <CardContent>
            <ul class="divide-y"><li v-for="r in data?.by_type || []" :key="r.name" class="flex justify-between py-2.5 text-sm"><span>{{ r.name }}</span><span class="tabular font-medium">{{ formatCurrency(r.value) }}</span></li></ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Collections by payment mode</CardTitle></CardHeader>
          <CardContent>
            <ul class="divide-y"><li v-for="r in data?.by_mode || []" :key="r.name" class="flex justify-between py-2.5 text-sm"><span>{{ r.name }} <span class="text-muted-foreground">· {{ r.count }}</span></span><span class="tabular font-medium">{{ formatCurrency(r.value) }}</span></li></ul>
          </CardContent>
        </Card>
      </div>
      <h2 class="mb-3 mt-6 font-semibold">Monthly detail</h2>
      <DataTable
        :columns="[
          { key: 'month', label: 'Month' },
          { key: 'property', label: 'Property' },
          { key: 'invoices', label: 'Invoices', align: 'right' },
          { key: 'invoiced', label: 'Invoiced', format: 'currency', align: 'right' },
          { key: 'collected', label: 'Collected', format: 'currency', align: 'right' },
          { key: 'outstanding', label: 'Outstanding', format: 'currency', align: 'right' },
        ]"
        :rows="(data?.monthly || []).map((r) => ({ ...r, key: r.month + r.property }))"
        :loading="loading"
        row-key="key"
      >
        <template #cell-month="{ value }">{{ formatMonth(value) }}</template>
      </DataTable>
    </template>
  </div>
</template>
