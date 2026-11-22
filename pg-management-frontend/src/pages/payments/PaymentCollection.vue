<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2, WifiOff, Wand2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { paymentService } from '@/services/payment.service'
import { useMutation } from '@/composables/useMutation'
import { useOnline } from '@/composables/useOnline'
import { useDashboardStore } from '@/stores/dashboard'
import { useTenantStore } from '@/stores/tenant'
import { formatCurrency } from '@/utils/currency'
import { dueLabel, formatMonth, today } from '@/utils/date'
import { positive, required, requestId, validate } from '@/utils/validation'
import type { Invoice, PaymentMode } from '@/types'

const route = useRoute()
const router = useRouter()
const online = useOnline()
const dashboard = useDashboardStore()
const tenantStore = useTenantStore()
const MODES: PaymentMode[] = ['UPI', 'Cash', 'Bank Transfer', 'Card', 'Cheque']

const form = reactive({ tenant: (route.query.tenant as string) || '', amount: null as number | null, mode: 'UPI' as PaymentMode, payment_date: today(), reference_no: '', remarks: '' })
const errors = ref<Record<string, string>>({})
const invoices = ref<Invoice[]>([])
const loadingInvoices = ref(false)
const alloc = reactive<Record<string, { on: boolean; amount: number }>>({})
// one idempotency key per payment attempt – retries/double taps never create duplicates
let clientRequestId = requestId()

async function loadInvoices() {
  invoices.value = []
  for (const k of Object.keys(alloc)) delete alloc[k]
  if (!form.tenant) return
  loadingInvoices.value = true
  try {
    invoices.value = await paymentService.outstanding(form.tenant)
    const focus = route.query.invoice as string
    for (const inv of invoices.value) alloc[inv.name] = { on: focus ? inv.name === focus : true, amount: inv.outstanding_amount }
    form.amount = selectedTotal.value || null
  } finally {
    loadingInvoices.value = false
  }
}
watch(() => form.tenant, loadInvoices)
onMounted(loadInvoices)

const selectedTotal = computed(() => invoices.value.reduce((s, i) => s + (alloc[i.name]?.on ? Number(alloc[i.name].amount) || 0 : 0), 0))
const totalDue = computed(() => invoices.value.reduce((s, i) => s + i.outstanding_amount, 0))
const unallocated = computed(() => Math.max(0, (Number(form.amount) || 0) - selectedTotal.value))

function autoAllocate() {
  let remaining = Number(form.amount) || 0
  for (const inv of invoices.value) {
    const a = Math.min(remaining, inv.outstanding_amount)
    alloc[inv.name] = { on: a > 0, amount: Math.round(a * 100) / 100 }
    remaining -= a
  }
}

const collect = useMutation(paymentService.collect)
async function submit() {
  errors.value = validate(form, { tenant: [required('Tenant')], amount: [required('Amount'), positive('Amount')], payment_date: [required('Date')] })
  if (form.mode !== 'Cash' && form.mode !== 'Card' && !form.reference_no.trim()) errors.value.reference_no = 'Reference / UTR is required for this mode'
  if (selectedTotal.value > (Number(form.amount) || 0) + 0.001) errors.value.amount = 'Allocated total exceeds the amount received'
  for (const inv of invoices.value) {
    const a = alloc[inv.name]
    if (a?.on && (a.amount <= 0 || a.amount > inv.outstanding_amount)) errors.value.alloc = `Allocation for ${inv.name} must be between 0 and ${inv.outstanding_amount}`
  }
  if (Object.keys(errors.value).length) return
  const res = await collect.run({
    tenant: form.tenant,
    amount: Number(form.amount),
    mode: form.mode,
    payment_date: form.payment_date,
    reference_no: form.reference_no || undefined,
    remarks: form.remarks || undefined,
    allocations: invoices.value.filter((i) => alloc[i.name]?.on).map((i) => ({ invoice: i.name, allocated_amount: Number(alloc[i.name].amount) })),
    client_request_id: clientRequestId,
  })
  if (res) {
    clientRequestId = requestId()
    dashboard.invalidate()
    tenantStore.invalidate(form.tenant)
    router.replace({ path: `/payments/${res.data.name}`, query: { new: '1' } })
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader title="Collect payment" description="Record money received and settle invoices." back />
    <div v-if="!online" role="alert" class="mb-4 flex items-center gap-2 rounded-xl border border-warning/30 bg-warning-soft p-3 text-sm text-warning">
      <WifiOff class="size-4" />You're offline. Payments can only be recorded once the server confirms them.
    </div>
    <form class="space-y-5" novalidate @submit.prevent="submit">
      <Card>
        <CardHeader><CardTitle>Tenant</CardTitle></CardHeader>
        <CardContent>
          <FormField v-slot="{ id, invalid }" :error="errors.tenant">
            <SearchSelect :id="id" v-model="form.tenant" doctype="PG Tenant" :filters="{ status: ['in', ['Active', 'On Notice', 'Vacated']] }" :invalid="invalid" placeholder="Search by name or mobile" />
          </FormField>
        </CardContent>
      </Card>

      <Card v-if="form.tenant">
        <CardHeader>
          <div><CardTitle>Outstanding invoices</CardTitle><CardDescription>Total due {{ formatCurrency(totalDue) }}</CardDescription></div>
          <Button v-if="invoices.length > 1" variant="ghost" size="sm" type="button" @click="autoAllocate"><Wand2 />Oldest first</Button>
        </CardHeader>
        <CardContent>
          <p v-if="loadingInvoices" class="text-sm text-muted-foreground">Loading…</p>
          <EmptyState v-else-if="!invoices.length" compact :icon="CheckCircle2" title="No dues" description="This tenant has no outstanding invoices. You can still record an advance." />
          <ul v-else class="divide-y">
            <li v-for="inv in invoices" :key="inv.name" class="flex flex-wrap items-center gap-3 py-3">
              <Checkbox :id="`a-${inv.name}`" v-model="alloc[inv.name].on" />
              <label :for="`a-${inv.name}`" class="min-w-0 flex-1 cursor-pointer">
                <span class="block text-sm font-medium">{{ formatMonth(inv.period_start) }} <span class="font-normal text-muted-foreground">· {{ inv.name }}</span></span>
                <span class="flex items-center gap-2 text-xs text-muted-foreground"><StatusBadge :status="inv.status" />{{ dueLabel(inv.due_date) }} · due {{ formatCurrency(inv.outstanding_amount) }}</span>
              </label>
              <Input v-model.number="alloc[inv.name].amount" type="number" min="0" :max="inv.outstanding_amount" step="0.01" :disabled="!alloc[inv.name].on" class="w-32 text-right" :aria-label="`Allocate to ${inv.name}`" />
            </li>
          </ul>
          <p v-if="errors.alloc" class="mt-2 text-xs font-medium text-destructive">{{ errors.alloc }}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Payment details</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id, invalid }" label="Amount received" required :error="errors.amount" class="sm:col-span-2">
            <Input :id="id" v-model.number="form.amount" type="number" min="0" step="0.01" inputmode="decimal" class="h-12 text-lg font-semibold" :aria-invalid="invalid" />
          </FormField>
          <fieldset class="sm:col-span-2">
            <legend class="mb-1.5 text-[13px] font-medium">Mode</legend>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="m in MODES"
                :key="m"
                type="button"
                :aria-pressed="form.mode === m"
                :class="['h-10 rounded-lg border px-4 text-sm font-medium transition', form.mode === m ? 'border-primary bg-primary/10 text-primary' : 'bg-card hover:bg-muted']"
                @click="form.mode = m"
              >
                {{ m }}
              </button>
            </div>
          </fieldset>
          <FormField v-slot="{ id, invalid }" label="Reference / UTR" :required="form.mode !== 'Cash' && form.mode !== 'Card'" :error="errors.reference_no">
            <Input :id="id" v-model="form.reference_no" autocomplete="off" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Date" required :error="errors.payment_date">
            <Input :id="id" v-model="form.payment_date" type="date" :max="today()" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id }" label="Remarks" class="sm:col-span-2"><Textarea :id="id" v-model="form.remarks" rows="2" /></FormField>
        </CardContent>
      </Card>

      <div class="sticky bottom-20 rounded-xl border bg-card/95 p-4 backdrop-blur lg:bottom-4">
        <div class="mb-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
          <div><p class="text-xs text-muted-foreground">Receiving</p><p class="tabular font-semibold">{{ formatCurrency(form.amount || 0) }}</p></div>
          <div><p class="text-xs text-muted-foreground">Allocated</p><p class="tabular font-semibold">{{ formatCurrency(selectedTotal) }}</p></div>
          <div v-if="unallocated > 0"><p class="text-xs text-muted-foreground">Advance (unallocated)</p><p class="tabular font-semibold text-info">{{ formatCurrency(unallocated) }}</p></div>
        </div>
        <Button type="submit" size="lg" class="w-full" variant="success" :loading="collect.pending.value" :disabled="!online">
          Record payment{{ form.amount ? ` of ${formatCurrency(form.amount)}` : '' }}
        </Button>
      </div>
    </form>
  </div>
</template>
