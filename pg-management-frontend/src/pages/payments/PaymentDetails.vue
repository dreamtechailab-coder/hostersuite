<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Ban, CheckCircle2, Printer } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import DetailList from '@/components/common/DetailList.vue'
import { paymentService } from '@/services/payment.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { useDashboardStore } from '@/stores/dashboard'
import { formatCurrency } from '@/utils/currency'
import { formatDate, formatDateTime, formatMonth } from '@/utils/date'

const props = defineProps<{ name: string }>()
const route = useRoute()
const router = useRouter()
const { can } = usePermissions()
const { confirm } = useConfirm()
const dashboard = useDashboardStore()
const { data, loading, error, run } = useAsync(() => paymentService.get(props.name), { immediate: true })
const p = computed(() => data.value?.payment)
const cancel = useMutation((reason?: string) => paymentService.cancel(props.name, reason))
async function onCancel() {
  const res = await confirm({ title: 'Cancel this payment?', description: 'The allocated invoices will become due again. This is recorded in the audit trail.', destructive: true, confirmText: 'Cancel payment', cancelText: 'Keep', withReason: true, reasonLabel: 'Reason' })
  if (res.confirmed && (await cancel.run(res.reason))) {
    dashboard.invalidate()
    run()
  }
}
const printPage = () => window.print()
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data && p">
      <div v-if="route.query.new && p.docstatus === 1" class="mb-5 flex items-center gap-3 rounded-xl border border-success/30 bg-success-soft p-4 text-success print:hidden">
        <CheckCircle2 class="size-5" /><span class="text-sm font-medium">Payment recorded and confirmed by the server.</span>
      </div>
      <PageHeader :title="`Receipt ${p.name}`" :description="data.tenant.full_name" back="/payments" class="print:hidden">
        <template #badge><StatusBadge :status="p.docstatus === 2 ? 'Cancelled' : 'Paid'" /></template>
        <template #actions>
          <Button variant="outline" @click="printPage"><Printer />Print</Button>
          <Button v-if="p.docstatus === 1 && can('PG Payment', 'cancel')" variant="outline" :loading="cancel.pending.value" @click="onCancel"><Ban />Cancel</Button>
          <Button variant="ghost" @click="router.push(`/tenants/${p.tenant}`)">View tenant</Button>
        </template>
      </PageHeader>
      <Card>
        <CardContent class="p-6">
          <p class="text-xs uppercase tracking-wide text-muted-foreground">Amount received</p>
          <p :class="['tabular mt-1 text-3xl font-semibold', p.docstatus === 2 ? 'text-muted-foreground line-through' : 'text-success']">{{ formatCurrency(p.amount) }}</p>
          <div class="mt-6">
            <DetailList
              :cols="3"
              :items="[
                { label: 'Tenant', value: data.tenant.full_name },
                { label: 'Mobile', value: data.tenant.mobile },
                { label: 'Date', value: formatDate(p.payment_date) },
                { label: 'Mode', value: p.mode },
                { label: 'Reference', value: p.reference_no },
                { label: 'Property', value: p.property },
                { label: 'Received by', value: data.received_by_name },
                { label: 'Recorded', value: formatDateTime(p.creation) },
                { label: 'Unallocated (advance)', value: formatCurrency(p.unallocated_amount) },
              ]"
            />
          </div>
          <p v-if="p.remarks" class="mt-4 text-sm"><span class="block text-xs text-muted-foreground">Remarks</span>{{ p.remarks }}</p>
        </CardContent>
      </Card>
      <Card class="mt-5">
        <CardHeader><CardTitle>Applied to invoices</CardTitle></CardHeader>
        <CardContent>
          <p v-if="!p.allocations?.length" class="text-sm text-muted-foreground">Not allocated to any invoice (held as advance).</p>
          <ul class="divide-y">
            <li v-for="a in p.allocations" :key="a.invoice">
              <RouterLink :to="`/rent/invoices/${a.invoice}`" class="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 hover:bg-muted/50">
                <span class="text-sm"><span class="font-medium">{{ a.invoice }}</span><span class="text-muted-foreground"> · {{ formatMonth(a.period_start) }}</span></span>
                <span class="flex items-center gap-3"><StatusBadge :status="a.status" /><span class="tabular font-medium">{{ formatCurrency(a.allocated_amount) }}</span></span>
              </RouterLink>
            </li>
          </ul>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
