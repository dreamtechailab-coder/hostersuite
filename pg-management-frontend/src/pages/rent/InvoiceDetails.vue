<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { CreditCard, MessageCircle, Printer, Ban } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { rentService } from '@/services/rent.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { useAuthStore } from '@/stores/auth'
import { useDashboardStore } from '@/stores/dashboard'
import { formatCurrency } from '@/utils/currency'
import { dueLabel, formatDate, formatMonth } from '@/utils/date'

const props = defineProps<{ name: string }>()
const router = useRouter()
const auth = useAuthStore()
const dashboard = useDashboardStore()
const { can } = usePermissions()
const { confirm } = useConfirm()
const { data, loading, error, run } = useAsync(() => rentService.get(props.name), { immediate: true })
const printPage = () => window.print()
const inv = computed(() => data.value?.invoice)
const remind = useMutation(() => rentService.sendWhatsApp(props.name, 'Rent Reminder'))
const cancel = useMutation(() => rentService.cancel(props.name), { success: 'Invoice cancelled' })
async function onCancel() {
  const { confirmed } = await confirm({ title: 'Cancel this invoice?', description: 'Cancelled invoices are kept for audit but no longer count as dues. Linked electricity charges become billable again.', destructive: true, confirmText: 'Cancel invoice', cancelText: 'Keep' })
  if (confirmed && (await cancel.run())) {
    dashboard.invalidate()
    run()
  }
}
</script>

<template>
  <div class="mx-auto max-w-4xl">
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data && inv">
      <PageHeader :title="inv.name" :description="`${formatMonth(inv.period_start)} · ${data.tenant.full_name}`" back class="print:hidden">
        <template #badge><StatusBadge :status="inv.status" /></template>
        <template #actions>
          <Button variant="outline" @click="printPage"><Printer />Print</Button>
          <Button v-if="inv.docstatus === 1 && inv.outstanding_amount > 0 && auth.settings?.whatsapp_enabled && can('PG WhatsApp Message', 'create')" variant="outline" :loading="remind.pending.value" @click="remind.run()"><MessageCircle />Remind</Button>
          <Button v-if="inv.docstatus === 1 && !inv.paid_amount && can('PG Rent Invoice', 'cancel')" variant="outline" :loading="cancel.pending.value" @click="onCancel"><Ban />Cancel</Button>
          <Button v-if="inv.docstatus === 1 && inv.outstanding_amount > 0 && can('PG Payment', 'create')" @click="router.push({ path: '/payments/collect', query: { tenant: inv.tenant, invoice: inv.name } })"><CreditCard />Collect {{ formatCurrency(inv.outstanding_amount) }}</Button>
        </template>
      </PageHeader>

      <Card class="print:border-0 print:shadow-none">
        <CardContent class="p-6 sm:p-8">
          <div class="flex flex-col justify-between gap-6 sm:flex-row">
            <div>
              <p class="text-lg font-semibold">{{ data.property.property_name }}</p>
              <p class="text-sm text-muted-foreground">{{ [data.property.address_line, data.property.city].filter(Boolean).join(', ') }}</p>
              <p v-if="data.property.phone" class="text-sm text-muted-foreground">{{ data.property.phone }}</p>
            </div>
            <div class="sm:text-right">
              <p class="text-xs uppercase tracking-wide text-muted-foreground">Rent invoice</p>
              <p class="font-semibold">{{ inv.name }}</p>
              <p class="text-sm text-muted-foreground">Issued {{ formatDate(inv.invoice_date) }}</p>
            </div>
          </div>
          <div class="mt-8 grid gap-6 sm:grid-cols-3">
            <div>
              <p class="text-xs text-muted-foreground">Billed to</p>
              <p class="font-medium">{{ data.tenant.full_name }}</p>
              <p class="text-sm text-muted-foreground">{{ data.tenant.mobile }}</p>
              <p v-if="data.room_number" class="text-sm text-muted-foreground">Room {{ data.room_number }}</p>
            </div>
            <div>
              <p class="text-xs text-muted-foreground">Period</p>
              <p class="font-medium">{{ formatDate(inv.period_start) }} – {{ formatDate(inv.period_end) }}</p>
            </div>
            <div>
              <p class="text-xs text-muted-foreground">Due date</p>
              <p class="font-medium">{{ formatDate(inv.due_date) }}</p>
              <p v-if="inv.outstanding_amount > 0 && inv.docstatus === 1" :class="['text-sm', inv.status === 'Overdue' ? 'text-destructive' : 'text-muted-foreground']">{{ dueLabel(inv.due_date) }}</p>
            </div>
          </div>
          <table class="mt-8 w-full text-sm">
            <thead class="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr><th class="py-2 font-medium">Description</th><th class="py-2 font-medium">Type</th><th class="py-2 text-right font-medium">Amount</th></tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="item in inv.items" :key="item.name">
                <td class="py-3">{{ item.description }}</td>
                <td class="py-3 text-muted-foreground">{{ item.item_type }}</td>
                <td class="tabular py-3 text-right">{{ formatCurrency(item.amount) }}</td>
              </tr>
            </tbody>
          </table>
          <div class="ml-auto mt-4 w-full max-w-xs space-y-2 border-t pt-4 text-sm">
            <div class="flex justify-between"><span class="text-muted-foreground">Total</span><span class="tabular font-medium">{{ formatCurrency(inv.total_amount) }}</span></div>
            <div class="flex justify-between"><span class="text-muted-foreground">Paid</span><span class="tabular text-success">− {{ formatCurrency(inv.paid_amount) }}</span></div>
            <div class="flex justify-between border-t pt-2 text-base font-semibold"><span>Balance due</span><span class="tabular">{{ formatCurrency(inv.outstanding_amount) }}</span></div>
          </div>
        </CardContent>
      </Card>

      <Card v-if="data.payments.length" class="mt-5 print:hidden">
        <CardHeader><CardTitle>Payments received</CardTitle></CardHeader>
        <CardContent>
          <ul class="divide-y">
            <li v-for="p in data.payments" :key="p.name">
              <RouterLink :to="`/payments/${p.name}`" class="-mx-2 flex items-center justify-between rounded-lg px-2 py-2.5 text-sm hover:bg-muted/50">
                <span>{{ formatDate(p.payment_date) }} · {{ p.mode }}<span v-if="p.reference_no" class="text-muted-foreground"> · {{ p.reference_no }}</span></span>
                <span class="tabular font-medium text-success">{{ formatCurrency(p.allocated_amount) }}</span>
              </RouterLink>
            </li>
          </ul>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
