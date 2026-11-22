<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { NativeSelect } from '@/components/ui/select'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { occupancyService } from '@/services/tenant.service'
import { roomService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { useDashboardStore } from '@/stores/dashboard'
import { between, nonNegative, positive, required, validate } from '@/utils/validation'
import { today } from '@/utils/date'
import { formatCurrency } from '@/utils/currency'
import type { Room } from '@/types'

const props = defineProps<{
  bed?: string
  room?: Room | null
  tenant?: string
  tenantLabel?: string
  booking?: string
  property?: string
}>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ done: [] }>()
const router = useRouter()
const { can } = usePermissions()
const propertyStore = usePropertyStore()
const dashboard = useDashboardStore()

const form = reactive({ tenant: '', bed: '', check_in_date: today(), monthly_rent: null as number | null, security_deposit: null as number | null, rent_due_day: 5, generate_invoice: true })
const errors = ref<Record<string, string>>({})
const rooms = ref<Room[]>([])
const bedOptions = computed(() =>
  rooms.value.flatMap((r) =>
    (r.beds || [])
      .filter((b) => b.status === 'Vacant' || (props.booking && b.reserved_booking === props.booking))
      .map((b) => ({ value: b.name, label: `Room ${r.room_number} · Bed ${b.bed_label} (${formatCurrency(r.rent_per_bed)})` })),
  ),
)
const selectedRoom = computed(() => props.room || rooms.value.find((r) => r.beds?.some((b) => b.name === form.bed)) || null)

watch(open, async (o) => {
  if (!o) return
  errors.value = {}
  Object.assign(form, { tenant: props.tenant || '', bed: props.bed || '', check_in_date: today(), monthly_rent: null, security_deposit: null, rent_due_day: 5, generate_invoice: can('PG Rent Invoice', 'create') })
  if (!props.bed) rooms.value = await roomService.board({ property: props.property || propertyStore.filter })
})
watch(selectedRoom, (r) => {
  if (r) {
    form.monthly_rent = r.rent_per_bed
    form.security_deposit = r.security_deposit ?? 0
  }
}, { immediate: true })

const checkIn = useMutation(occupancyService.checkIn)
async function submit() {
  errors.value = validate(form, {
    tenant: [required('Tenant')], bed: [required('Bed')], check_in_date: [required('Check-in date')],
    monthly_rent: [required('Rent'), positive('Rent')], security_deposit: [nonNegative('Deposit')], rent_due_day: [between(1, 28, 'Due day')],
  })
  if (Object.keys(errors.value).length) return
  const res = await checkIn.run({
    tenant: form.tenant, bed: form.bed, check_in_date: form.check_in_date, monthly_rent: form.monthly_rent, security_deposit: form.security_deposit,
    rent_due_day: form.rent_due_day, booking: props.booking, generate_invoice: form.generate_invoice ? 1 : 0,
  })
  if (res) {
    dashboard.invalidate()
    open.value = false
    emit('done')
    if (res.data.invoice) router.push(`/rent/invoices/${res.data.invoice}`)
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" title="Check in tenant" description="Assign a bed and start the tenancy." size="lg">
    <form id="checkin-form" class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Tenant" required :error="errors.tenant" class="sm:col-span-2">
        <SearchSelect
          :id="id"
          v-model="form.tenant"
          doctype="PG Tenant"
          :filters="{ status: ['in', ['Prospective', 'Vacated']] }"
          :initial-label="tenantLabel"
          :disabled="!!tenant"
          :invalid="invalid"
          placeholder="Search prospective tenants…"
        />
        <p v-if="!tenant" class="text-xs text-muted-foreground">New person? <RouterLink to="/tenants/new" class="font-medium text-primary hover:underline">Create a tenant first</RouterLink></p>
      </FormField>
      <FormField v-if="!bed" v-slot="{ id, invalid }" label="Bed" required :error="errors.bed" class="sm:col-span-2">
        <SearchSelect :id="id" v-model="form.bed" :options="bedOptions" :invalid="invalid" placeholder="Choose a vacant bed" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Check-in date" required :error="errors.check_in_date">
        <Input :id="id" v-model="form.check_in_date" type="date" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Rent due day" :error="errors.rent_due_day" hint="Day of each month">
        <NativeSelect :id="id" v-model.number="form.rent_due_day" :options="Array.from({ length: 28 }, (_, i) => ({ value: i + 1, label: String(i + 1) }))" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Monthly rent" required :error="errors.monthly_rent">
        <Input :id="id" v-model.number="form.monthly_rent" type="number" min="0" inputmode="decimal" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Security deposit" :error="errors.security_deposit">
        <Input :id="id" v-model.number="form.security_deposit" type="number" min="0" inputmode="decimal" :aria-invalid="invalid" />
      </FormField>
      <label v-if="can('PG Rent Invoice', 'create')" class="flex items-center gap-2 text-sm sm:col-span-2">
        <Checkbox v-model="form.generate_invoice" />Generate this month's (pro-rated) rent invoice now
      </label>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="checkin-form" :loading="checkIn.pending.value">Check in</Button>
    </template>
  </ModalDialog>
</template>
