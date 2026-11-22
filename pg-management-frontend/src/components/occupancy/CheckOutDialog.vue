<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { NativeSelect } from '@/components/ui/select'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import { occupancyService } from '@/services/tenant.service'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { useDashboardStore } from '@/stores/dashboard'
import { formatCurrency } from '@/utils/currency'
import { today } from '@/utils/date'
import type { Occupancy } from '@/types'

const props = defineProps<{ occupancy: Occupancy | null; mode: 'notice' | 'checkout' }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ done: [] }>()
const { can } = usePermissions()
const dashboard = useDashboardStore()
const form = reactive({ date: today(), expected: '', deposit_status: 'Refunded', refund: 0, final_invoice: true })
const error = ref('')
watch(open, (o) => {
  if (!o || !props.occupancy) return
  error.value = ''
  Object.assign(form, { date: today(), expected: props.occupancy.expected_check_out || '', deposit_status: props.occupancy.security_deposit ? 'Refunded' : 'Not Collected', refund: props.occupancy.security_deposit || 0, final_invoice: can('PG Rent Invoice', 'create') })
})
const notice = useMutation(() => occupancyService.giveNotice(props.occupancy!.name, form.date, form.expected || undefined))
const checkout = useMutation(() =>
  occupancyService.checkOut({
    name: props.occupancy!.name, check_out_date: form.date, deposit_status: form.deposit_status,
    deposit_refund_amount: form.deposit_status === 'Refunded' ? Number(form.refund) : 0, generate_final_invoice: form.final_invoice ? 1 : 0,
  }),
)
async function submit() {
  if (props.mode === 'checkout' && form.deposit_status === 'Refunded' && Number(form.refund) > Number(props.occupancy?.security_deposit || 0)) {
    error.value = 'Refund cannot exceed the deposit'
    return
  }
  const res = props.mode === 'notice' ? await notice.run() : await checkout.run()
  if (res) {
    dashboard.invalidate()
    open.value = false
    emit('done')
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" :title="mode === 'notice' ? 'Record notice' : 'Check out tenant'" :description="occupancy?.tenant_name">
    <form id="checkout-form" class="space-y-4" @submit.prevent="submit">
      <template v-if="mode === 'notice'">
        <FormField v-slot="{ id }" label="Notice date"><Input :id="id" v-model="form.date" type="date" /></FormField>
        <FormField v-slot="{ id }" label="Expected check-out"><Input :id="id" v-model="form.expected" type="date" :min="form.date" /></FormField>
      </template>
      <template v-else>
        <FormField v-slot="{ id }" label="Check-out date"><Input :id="id" v-model="form.date" type="date" :min="occupancy?.check_in_date" /></FormField>
        <div class="rounded-lg bg-muted/50 px-3 py-2.5 text-sm">Security deposit held: <strong class="tabular">{{ formatCurrency(occupancy?.security_deposit) }}</strong></div>
        <FormField v-slot="{ id }" label="Deposit">
          <NativeSelect :id="id" v-model="form.deposit_status" :options="[{ value: 'Refunded', label: 'Refunded now' }, { value: 'Adjusted', label: 'Adjusted against dues' }, { value: 'Held', label: 'Refund later (track as payable)' }, { value: 'Not Collected', label: 'Not collected' }]" />
        </FormField>
        <FormField v-if="form.deposit_status === 'Refunded'" v-slot="{ id, invalid }" label="Refund amount" :error="error">
          <Input :id="id" v-model.number="form.refund" type="number" min="0" :max="occupancy?.security_deposit" :aria-invalid="invalid" />
        </FormField>
        <label v-if="can('PG Rent Invoice', 'create')" class="flex items-center gap-2 text-sm"><Checkbox v-model="form.final_invoice" />Generate final pro-rated invoice (incl. unbilled electricity)</label>
      </template>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="checkout-form" :variant="mode === 'checkout' ? 'destructive' : 'default'" :loading="notice.pending.value || checkout.pending.value">
        {{ mode === 'notice' ? 'Save notice' : 'Check out' }}
      </Button>
    </template>
  </ModalDialog>
</template>
