<script setup lang="ts">
import { ref, watch } from 'vue'
import { AlertTriangle, CheckCircle2, FileText, Receipt, Send, Sparkles } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import InvoiceCard from '@/components/rent/InvoiceCard.vue'
import GenerateInvoicesDialog from '@/components/rent/GenerateInvoicesDialog.vue'
import { rentService } from '@/services/rent.service'
import { whatsappService } from '@/services/whatsapp.service'
import { resource } from '@/services/resource.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from '@/composables/useConfirm'
import { formatCurrency, formatPercent } from '@/utils/currency'
import { formatMonth } from '@/utils/date'
import type { Invoice } from '@/types'

const property = usePropertyStore()
const auth = useAuthStore()
const { can } = usePermissions()
const { confirm } = useConfirm()
const month = ref(new Date().toISOString().slice(0, 7))
const summary = useAsync(() => rentService.summary(property.filter, `${month.value}-01`))
const overdue = useAsync(() =>
  resource.list<Invoice>('PG Rent Invoice', {
    filters: { docstatus: 1, status: 'Overdue', ...(property.filter ? { property: property.filter } : {}) },
    order_by: 'due_date asc',
    page_size: 6,
  }),
)
function load() {
  summary.run()
  overdue.run()
}
watch([() => property.filter, month], load, { immediate: true })
const genOpen = ref(false)
const remind = useMutation(() => whatsappService.bulkReminders(property.filter))
async function remindAll() {
  const { confirmed } = await confirm({ title: 'Send WhatsApp reminders?', description: 'A reminder will be queued for every tenant with an outstanding invoice who has opted in.', confirmText: 'Send reminders' })
  if (confirmed) remind.run()
}
</script>

<template>
  <div>
    <PageHeader title="Rent" :description="`Collections for ${formatMonth(month)} · ${property.label}`">
      <template #actions>
        <Input v-model="month" type="month" class="w-40" aria-label="Month" />
        <Button v-if="auth.settings?.whatsapp_enabled && can('PG WhatsApp Message', 'create')" variant="outline" :loading="remind.pending.value" @click="remindAll"><Send />Remind all</Button>
        <Button v-if="can('PG Rent Invoice', 'create')" @click="genOpen = true"><Sparkles />Generate invoices</Button>
      </template>
    </PageHeader>
    <ErrorState v-if="summary.error.value" :error="summary.error.value" @retry="load" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Invoiced" :value="formatCurrency(summary.data.value?.totals.invoiced)" :hint="`${summary.data.value?.totals.invoices ?? 0} invoices`" :icon="FileText" :loading="summary.loading.value" to="/rent/invoices" />
        <StatCard
          label="Collected"
          :value="formatCurrency(summary.data.value?.totals.collected)"
          :hint="summary.data.value?.totals.invoiced ? `${formatPercent((summary.data.value.totals.collected * 100) / summary.data.value.totals.invoiced)} collection rate` : undefined"
          :progress="summary.data.value?.totals.invoiced ? (summary.data.value.totals.collected * 100) / summary.data.value.totals.invoiced : 0"
          :icon="CheckCircle2"
          tone="success"
          :loading="summary.loading.value"
        />
        <StatCard label="Pending this month" :value="formatCurrency(summary.data.value?.totals.outstanding)" :icon="Receipt" tone="warning" :loading="summary.loading.value" />
        <StatCard label="Overdue (all months)" :value="formatCurrency(summary.data.value?.overdue.amount)" :hint="`${summary.data.value?.overdue.count ?? 0} invoices`" :icon="AlertTriangle" :tone="summary.data.value?.overdue.amount ? 'danger' : 'success'" :loading="summary.loading.value" to="/finance/receivables" />
      </div>

      <div v-if="summary.data.value?.pending_occupancies" class="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-warning/30 bg-warning-soft p-4 text-sm">
        <AlertTriangle class="size-5 text-warning" />
        <span class="flex-1"><strong>{{ summary.data.value.pending_occupancies }}</strong> tenant(s) have not been invoiced for {{ formatMonth(month) }}.</span>
        <Button v-if="can('PG Rent Invoice', 'create')" size="sm" @click="genOpen = true">Generate now</Button>
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Status breakdown</CardTitle></CardHeader>
          <CardContent>
            <EmptyState v-if="!summary.data.value?.by_status.length" compact title="No invoices this month" />
            <ul class="divide-y">
              <li v-for="s in summary.data.value?.by_status" :key="s.status" class="flex items-center justify-between py-2.5">
                <RouterLink :to="{ path: '/rent/invoices', query: { status: s.status, month } }" class="hover:underline"><StatusBadge :status="s.status" /></RouterLink>
                <span class="text-sm"><span class="tabular font-medium">{{ s.count }}</span><span v-if="s.outstanding" class="tabular text-muted-foreground"> · {{ formatCurrency(s.outstanding) }} due</span></span>
              </li>
            </ul>
          </CardContent>
        </Card>
        <div class="lg:col-span-2">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="font-semibold">Overdue invoices</h2>
            <Button variant="link" size="sm" as-child><RouterLink to="/rent/invoices?status=Overdue">View all</RouterLink></Button>
          </div>
          <EmptyState v-if="!overdue.loading.value && !overdue.data.value?.data.length" compact :icon="CheckCircle2" title="Nothing overdue" description="Great – every tenant is up to date." class="rounded-xl border bg-card" />
          <div class="grid gap-3 sm:grid-cols-2">
            <InvoiceCard v-for="inv in overdue.data.value?.data" :key="inv.name" :invoice="inv" />
          </div>
        </div>
      </div>
    </template>
    <GenerateInvoicesDialog v-model:open="genOpen" :month="`${month}-01`" @done="load" />
  </div>
</template>
