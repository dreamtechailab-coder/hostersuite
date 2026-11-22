<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { propertyService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { required, validate } from '@/utils/validation'
import type { Floor } from '@/types'

const props = defineProps<{ floor?: Floor | null; property?: string; building?: string }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [f: Floor] }>()
const form = reactive<Partial<Floor>>({})
const errors = ref<Record<string, string>>({})
watch(open, (o) => {
  if (!o) return
  errors.value = {}
  Object.assign(form, { name: undefined, property: props.property || '', building: props.building || '', floor_name: '', floor_number: 0, ...(props.floor || {}) })
})
watch(() => form.property, (p, old) => old && p !== old && (form.building = ''))
const save = useMutation(propertyService.saveFloor, { success: 'Floor saved' })
async function submit() {
  errors.value = validate(form, { property: [required('Property')], building: [required('Building')], floor_name: [required('Floor name')] })
  if (Object.keys(errors.value).length) return
  const res = await save.run(form)
  if (res) {
    emit('saved', res.data)
    open.value = false
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" :title="floor?.name ? 'Edit floor' : 'Add floor'">
    <form id="floor-form" class="space-y-4" @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property">
        <SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" :disabled="!!floor?.name" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Building" required :error="errors.building">
        <SearchSelect :id="id" v-model="form.building" doctype="PG Building" :filters="{ property: form.property }" :disabled="!form.property" :invalid="invalid" />
      </FormField>
      <div class="grid grid-cols-3 gap-3">
        <FormField v-slot="{ id, invalid }" label="Floor name" required :error="errors.floor_name" class="col-span-2">
          <Input :id="id" v-model="form.floor_name" placeholder="e.g. Ground floor" :aria-invalid="invalid" />
        </FormField>
        <FormField v-slot="{ id }" label="Level"><Input :id="id" v-model.number="form.floor_number" type="number" inputmode="numeric" /></FormField>
      </div>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="floor-form" :loading="save.pending.value">Save</Button>
    </template>
  </ModalDialog>
</template>
