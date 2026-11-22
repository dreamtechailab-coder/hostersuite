<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { bookingService } from '@/services/tenant.service'
import { roomService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { usePropertyStore } from '@/stores/property'
import { nonNegative, required, validate } from '@/utils/validation'
import { today } from '@/utils/date'
import type { Room } from '@/types'

const router = useRouter()
const propertyStore = usePropertyStore()
const form = reactive({ tenant: '', property: propertyStore.filter || '', room: '', bed: '', booking_date: today(), expected_check_in: today(), advance_amount: 0, notes: '' })
const errors = ref<Record<string, string>>({})
const rooms = ref<Room[]>([])
watch(() => form.property, async (p) => {
  form.room = ''
  rooms.value = p ? await roomService.board({ property: p, vacant_only: 1 }) : []
}, { immediate: true })
watch(() => form.room, () => (form.bed = ''))
const roomOptions = computed(() => rooms.value.map((r) => ({ value: r.name, label: `Room ${r.room_number} · ${r.room_type} · ${(r.beds || []).filter((b) => b.status === 'Vacant').length} vacant` })))
const bedOptions = computed(() => (rooms.value.find((r) => r.name === form.room)?.beds || []).filter((b) => b.status === 'Vacant').map((b) => ({ value: b.name, label: `Bed ${b.bed_label}` })))
const save = useMutation(bookingService.save, { success: 'Booking created' })
async function submit() {
  errors.value = validate(form, { tenant: [required('Tenant')], property: [required('Property')], room: [required('Room')], expected_check_in: [required('Check-in date')], advance_amount: [nonNegative('Advance')] })
  if (form.expected_check_in < form.booking_date) errors.value.expected_check_in = 'Cannot be before booking date'
  if (Object.keys(errors.value).length) return
  if (await save.run({ ...form, bed: form.bed || undefined })) router.replace('/bookings')
}
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <PageHeader title="New booking" description="Reserve a room (and optionally a specific bed) for a tenant." back="/bookings" />
    <Card>
      <CardContent>
        <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
          <FormField v-slot="{ id, invalid }" label="Tenant" required :error="errors.tenant" class="sm:col-span-2">
            <SearchSelect :id="id" v-model="form.tenant" doctype="PG Tenant" :filters="{ status: ['in', ['Prospective', 'Vacated']] }" :invalid="invalid" />
            <p class="text-xs text-muted-foreground">Not listed? <RouterLink to="/tenants/new" class="font-medium text-primary hover:underline">Add a tenant</RouterLink></p>
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property" class="sm:col-span-2">
            <SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Room" required :error="errors.room">
            <SearchSelect :id="id" v-model="form.room" :options="roomOptions" :disabled="!form.property" :invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id }" label="Bed" hint="Confirming reserves this bed">
            <SearchSelect :id="id" v-model="form.bed" :options="bedOptions" :disabled="!form.room" placeholder="Any bed" />
          </FormField>
          <FormField v-slot="{ id }" label="Booking date"><Input :id="id" v-model="form.booking_date" type="date" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Expected check-in" required :error="errors.expected_check_in">
            <Input :id="id" v-model="form.expected_check_in" type="date" :min="form.booking_date" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Advance received" :error="errors.advance_amount">
            <Input :id="id" v-model.number="form.advance_amount" type="number" min="0" inputmode="decimal" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id }" label="Notes" class="sm:col-span-2"><Textarea :id="id" v-model="form.notes" rows="2" /></FormField>
          <div class="flex justify-end gap-2 sm:col-span-2">
            <Button variant="outline" @click="router.back()">Cancel</Button>
            <Button type="submit" :loading="save.pending.value">Create booking</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
