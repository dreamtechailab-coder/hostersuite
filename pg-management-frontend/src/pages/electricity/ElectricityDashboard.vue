<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Gauge, Zap, Receipt, AlertCircle, Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import ReadingDialog from '@/components/electricity/ReadingDialog.vue'
import { electricityService } from '@/services/rent.service'
import { useAsync } from '@/composables/useAsync'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { baseOption, type ChartTheme } from '@/lib/chart'
import { formatCurrency, formatNumber } from '@/utils/currency'
import { formatDate, formatMonth } from '@/utils/date'
import type { Meter } from '@/types'

const property = usePropertyStore()
const { can } = usePermissions()
const month = ref(new Date().toISOString().slice(0, 7))
const summary = useAsync(() => electricityService.summary(property.filter, `${month.value}-01`))
const meters = useAsync(() => electricityService.meters(property.filter, `${month.value}-01`))
const load = () => (summary.run(), meters.run())
watch([() => property.filter, month], load, { immediate: true })
const pending = computed(() => (meters.data.value || []).filter((m) => m.is_active && !m.reading_this_month))
const sel = ref<Meter | null>(null)
const open = ref(false)
function record(m: Meter) {
  sel.value = m
  open.value = true
}
function buildTrend(t: ChartTheme) {
  const tr = summary.data.value?.trend || []
  return {
    ...baseOption(t),
    grid: { left: 8, right: 8, top: 12, bottom: 4, containLabel: true },
    tooltip: { ...baseOption(t).tooltip, trigger: 'axis', valueFormatter: (v: number) => `${formatNumber(v, 1)} units` },
    xAxis: { type: 'category', data: tr.map((r) => formatMonth(r.month, true)), axisTick: { show: false }, axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.text, fontSize: 11 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: t.grid } }, axisLabel: { color: t.text, fontSize: 11 } },
    series: [{ type: 'bar', name: 'Units', data: tr.map((r) => Number(r.units)), barMaxWidth: 28, itemStyle: { color: t.palette[0], borderRadius: [4, 4, 0, 0] } }],
  }
}
</script>

<template>
  <div>
    <PageHeader title="Electricity" :description="`Meter readings & sub-metered bills · ${formatMonth(month)}`">
      <template #actions>
        <Input v-model="month" type="month" class="w-40" aria-label="Month" />
        <Button variant="outline" as-child><RouterLink to="/electricity/bills"><Receipt />Bills</RouterLink></Button>
        <Button as-child><RouterLink to="/electricity/readings"><Gauge />Readings</RouterLink></Button>
      </template>
    </PageHeader>
    <ErrorState v-if="summary.error.value" :error="summary.error.value" @retry="load" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Units consumed" :value="formatNumber(summary.data.value?.units, 1)" :icon="Zap" tone="warning" :loading="summary.loading.value" />
        <StatCard label="Billed amount" :value="formatCurrency(summary.data.value?.amount)" :hint="`${summary.data.value?.readings ?? 0} readings`" :icon="Receipt" :loading="summary.loading.value" />
        <StatCard label="Not yet invoiced" :value="formatCurrency(summary.data.value?.unbilled_amount)" hint="Added to next rent invoice" :icon="AlertCircle" tone="info" :loading="summary.loading.value" />
        <StatCard label="Readings pending" :value="pending.length" :hint="`of ${summary.data.value?.active_meters ?? 0} active meters`" :icon="Gauge" :tone="pending.length ? 'danger' : 'success'" :loading="meters.loading.value" />
      </div>
      <div class="mt-5 grid gap-5 lg:grid-cols-5">
        <Card class="lg:col-span-3">
          <CardHeader>
            <div><CardTitle>Readings due this month</CardTitle><CardDescription>Tap a meter to record its reading</CardDescription></div>
          </CardHeader>
          <CardContent>
            <EmptyState v-if="!meters.loading.value && !(meters.data.value || []).length" compact :icon="Gauge" title="No meters yet">
              <Button v-if="can('PG Electricity Meter', 'create')" as-child><RouterLink to="/electricity/readings?addMeter=1"><Plus />Add meter</RouterLink></Button>
            </EmptyState>
            <EmptyState v-else-if="!pending.length && !meters.loading.value" compact title="All readings recorded" description="Every active meter has a reading this month." />
            <ul class="divide-y">
              <li v-for="m in pending" :key="m.name" class="flex items-center gap-3 py-2.5">
                <span class="flex size-9 items-center justify-center rounded-lg bg-warning-soft text-warning"><Gauge class="size-4" /></span>
                <span class="min-w-0 flex-1">
                  <span class="block text-sm font-medium">Room {{ m.room_number }} · {{ m.meter_number }}</span>
                  <span class="tabular block text-xs text-muted-foreground">Last {{ formatNumber(m.last_reading, 2) }} on {{ formatDate(m.last_reading_date) }}</span>
                </span>
                <Button v-if="can('PG Meter Reading', 'create')" size="sm" @click="record(m)">Record</Button>
              </li>
            </ul>
          </CardContent>
        </Card>
        <Card class="lg:col-span-2">
          <CardHeader><div><CardTitle>Consumption</CardTitle><CardDescription>Units per month</CardDescription></div></CardHeader>
          <CardContent>
            <EmptyState v-if="!summary.data.value?.trend.length" compact title="No readings yet" />
            <BaseChart v-else :build="buildTrend" :height="240" label="Monthly electricity units" />
          </CardContent>
        </Card>
      </div>
    </template>
    <ReadingDialog v-model:open="open" :meter="sel" @saved="load" />
  </div>
</template>
