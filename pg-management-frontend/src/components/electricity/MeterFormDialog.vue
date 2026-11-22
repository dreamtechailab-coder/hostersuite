<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { electricityService } from '@/services/rent.service'
import { useMutation } from '@/composables/useMutation'
import { usePropertyStore } from '@/stores/property'
import { nonNegative, positive, required, validate } from '@/utils/validation'
import type { Meter } from '@/types'

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()
const property = usePropertyStore()
const form = reactive<Partial<Meter>>({})
const errors = ref<Record<string, string>>({})
watch(open, (o) => o && Object.assign(form, { property: property.filter || '', room: '', meter_number: '', rate_per_unit: 8, initial_reading: 0, is_active: 1 }))
watch(() => form.property, () => (form.room = ''))
const save = useMutation(electricityService.saveMeter, { success: 'Meter added' })
async function submit() {
  errors.value = validate(form, { property: [required('Property')], room: [required('Room')], meter_number: [required('Meter number')], rate_per_unit: [required('Rate'), positive('Rate')], initial_reading: [nonNegative('Reading')] })
  if (Object.keys(errors.value).length) return
  if (await save.run(form)) {
    emit('saved')
    open.value = false
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" title="Add electricity meter">
    <form id="meter-form" class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property"><SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" /></FormField>
      <FormField v-slot="{ id, invalid }" label="Room" required :error="errors.room"><SearchSelect :id="id" v-model="form.room" doctype="PG Room" :filters="{ property: form.property }" :disabled="!form.property" :invalid="invalid" /></FormField>
      <FormField v-slot="{ id, invalid }" label="Meter number" required :error="errors.meter_number"><Input :id="id" v-model="form.meter_number" :aria-invalid="invalid" /></FormField>
      <FormField v-slot="{ id, invalid }" label="Rate per unit" required :error="errors.rate_per_unit"><Input :id="id" v-model.number="form.rate_per_unit" type="number" step="0.01" min="0" :aria-invalid="invalid" /></FormField>
      <FormField v-slot="{ id, invalid }" label="Opening reading" :error="errors.initial_reading" class="sm:col-span-2"><Input :id="id" v-model.number="form.initial_reading" type="number" step="0.01" min="0" :aria-invalid="invalid" /></FormField>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="meter-form" :loading="save.pending.value">Add meter</Button>
    </template>
  </ModalDialog>
</template>
