<script setup lang="ts">
import { watch } from 'vue'
import { AlertTriangle, CheckCircle2, FileText, List, MessageCircle, Send, Settings, Users, XCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import BaseChart from '@/components/common/BaseChart.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { whatsappService } from '@/services/whatsapp.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { baseOption, type ChartTheme } from '@/lib/chart'
import { formatDate } from '@/utils/date'

const property = usePropertyStore()
const { can, hasRole } = usePermissions()
const { confirm } = useConfirm()
const { data, loading, error, run } = useAsync(() => whatsappService.dashboard(property.filter))
watch(() => property.filter, () => run(), { immediate: true })
const bulk = useMutation(() => whatsappService.bulkReminders(property.filter))
async function sendAll() {
  const { confirmed } = await confirm({ title: 'Send rent reminders to everyone with dues?', confirmText: 'Send' })
  if (confirmed && (await bulk.run())) run()
}
function build(t: ChartTheme) {
  const d = data.value?.daily || []
  return {
    ...baseOption(t),
    grid: { left: 8, right: 8, top: 36, bottom: 4, containLabel: true },
    legend: { top: 0, left: 0, icon: 'roundRect', itemWidth: 12, itemHeight: 4, textStyle: { color: t.text } },
    tooltip: { ...baseOption(t).tooltip, trigger: 'axis' },
    xAxis: { type: 'category', data: d.map((r) => formatDate(r.day, { day: 'numeric', month: 'short' })), axisTick: { show: false }, axisLine: { lineStyle: { color: t.axis } }, axisLabel: { color: t.text, fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: t.grid } }, axisLabel: { color: t.text, fontSize: 11 } },
    series: [
      { name: 'Sent', type: 'bar', stack: 'm', data: d.map((r) => Number(r.sent)), barMaxWidth: 18, itemStyle: { color: t.palette[0] } },
      { name: 'Failed', type: 'bar', stack: 'm', data: d.map((r) => Number(r.failed)), barMaxWidth: 18, itemStyle: { color: t.palette[1], borderRadius: [4, 4, 0, 0] } },
    ],
  }
}
</script>

<template>
  <div>
    <PageHeader title="WhatsApp" description="Automated reminders, receipts and tenant messaging (last 30 days).">
      <template #actions>
        <Button variant="outline" as-child><RouterLink to="/whatsapp/templates"><FileText />Templates</RouterLink></Button>
        <Button variant="outline" as-child><RouterLink to="/whatsapp/logs"><List />Logs</RouterLink></Button>
        <Button v-if="data?.enabled && can('PG WhatsApp Message', 'create')" :loading="bulk.pending.value" @click="sendAll"><Send />Send reminders</Button>
      </template>
    </PageHeader>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else-if="data">
      <div v-if="!data.enabled || !data.configured" class="mb-5 flex flex-wrap items-center gap-3 rounded-xl border border-warning/30 bg-warning-soft p-4 text-sm">
        <AlertTriangle class="size-5 text-warning" />
        <span class="flex-1">{{ !data.enabled ? 'WhatsApp messaging is turned off.' : 'WhatsApp Cloud API credentials are missing.' }} Messages will be logged as failed until it is configured.</span>
        <Button v-if="hasRole('PG Admin')" size="sm" as-child><RouterLink to="/settings/whatsapp"><Settings />Configure</RouterLink></Button>
      </div>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Sent" :value="data.by_status.Sent || 0" :icon="CheckCircle2" tone="success" :loading="loading" />
        <StatCard label="Failed" :value="data.by_status.Failed || 0" :icon="XCircle" :tone="data.by_status.Failed ? 'danger' : 'success'" to="/whatsapp/logs?status=Failed" :loading="loading" />
        <StatCard label="Queued" :value="data.by_status.Queued || 0" :icon="MessageCircle" tone="info" :loading="loading" />
        <StatCard label="Opted-in tenants" :value="data.opted_in_tenants" :hint="`${data.templates} active templates`" :icon="Users" :loading="loading" />
      </div>
      <Card class="mt-5">
        <CardHeader><div><CardTitle>Delivery activity</CardTitle><CardDescription>Messages per day</CardDescription></div></CardHeader>
        <CardContent>
          <EmptyState v-if="!data.daily.length" compact title="No messages in the last 30 days" />
          <BaseChart v-else :build="build" :height="240" label="WhatsApp messages sent and failed per day" />
        </CardContent>
      </Card>
    </template>
  </div>
</template>
