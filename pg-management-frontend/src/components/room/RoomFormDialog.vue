<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { roomService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { between, nonNegative, positive, required, validate } from '@/utils/validation'
import type { Room } from '@/types'

const props = defineProps<{ room?: Room | null; defaults?: Partial<Room> }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [r: Room] }>()
const CAPACITY: Record<string, number> = { Single: 1, Double: 2, Triple: 3, Quad: 4, Dormitory: 6 }
const form = reactive<Partial<Room>>({})
const errors = ref<Record<string, string>>({})
let hydrating = false
watch(open, (o) => {
  if (!o) return
  hydrating = true
  errors.value = {}
  Object.assign(form, {
    name: undefined, property: '', building: '', floor: '', room_number: '', room_type: 'Double', capacity: 2, rent_per_bed: undefined,
    security_deposit: undefined, is_ac: 0, attached_bathroom: 0, amenities: '', status: 'Available',
    ...(props.defaults || {}), ...(props.room || {}),
  })
  setTimeout(() => (hydrating = false))
})
watch(() => form.property, () => !hydrating && (form.building = ''))
watch(() => form.building, () => !hydrating && (form.floor = ''))
watch(() => form.room_type, (t) => !hydrating && t && (form.capacity = CAPACITY[t] ?? form.capacity))

const save = useMutation(roomService.save, { success: 'Room saved' })
async function submit() {
  errors.value = validate(form, {
    property: [required('Property')], building: [required('Building')], floor: [required('Floor')], room_number: [required('Room number')],
    capacity: [required('Beds'), between(1, 50, 'Beds')], rent_per_bed: [required('Rent'), positive('Rent')], security_deposit: [nonNegative('Deposit')],
  })
  if (Object.keys(errors.value).length) return
  const res = await save.run(form)
  if (res) {
    emit('saved', res.data)
    open.value = false
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" :title="room?.name ? `Edit room ${room.room_number}` : 'Add room'" description="Beds are created automatically from the bed count." size="lg">
    <form id="room-form" class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property">
        <SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" :disabled="!!room?.name" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Building" required :error="errors.building">
        <SearchSelect :id="id" v-model="form.building" doctype="PG Building" :filters="{ property: form.property }" :disabled="!form.property || !!room?.name" :invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Floor" required :error="errors.floor">
        <SearchSelect :id="id" v-model="form.floor" doctype="PG Floor" :filters="{ building: form.building }" :disabled="!form.building" :invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Room number" required :error="errors.room_number">
        <Input :id="id" v-model="form.room_number" placeholder="e.g. 101" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id }" label="Sharing type"><NativeSelect :id="id" v-model="form.room_type" :options="Object.keys(CAPACITY)" /></FormField>
      <FormField v-slot="{ id, invalid }" label="Beds" required :error="errors.capacity">
        <Input :id="id" v-model.number="form.capacity" type="number" min="1" max="50" inputmode="numeric" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Monthly rent per bed" required :error="errors.rent_per_bed">
        <Input :id="id" v-model.number="form.rent_per_bed" type="number" min="0" inputmode="decimal" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Security deposit per bed" :error="errors.security_deposit">
        <Input :id="id" v-model.number="form.security_deposit" type="number" min="0" inputmode="decimal" :aria-invalid="invalid" />
      </FormField>
      <div class="flex flex-wrap gap-6 sm:col-span-2">
        <label class="flex items-center gap-2 text-sm"><Checkbox :model-value="!!form.is_ac" @update:model-value="form.is_ac = $event ? 1 : 0" />Air conditioned</label>
        <label class="flex items-center gap-2 text-sm"><Checkbox :model-value="!!form.attached_bathroom" @update:model-value="form.attached_bathroom = $event ? 1 : 0" />Attached bathroom</label>
        <label v-if="room?.name" class="flex items-center gap-2 text-sm"><Checkbox :model-value="form.status === 'Maintenance'" @update:model-value="form.status = $event ? 'Maintenance' : 'Available'" />Under maintenance</label>
      </div>
      <FormField v-slot="{ id }" label="Amenities" class="sm:col-span-2"><Textarea :id="id" v-model="form.amenities" rows="2" /></FormField>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="room-form" :loading="save.pending.value">Save room</Button>
    </template>
  </ModalDialog>
</template>
