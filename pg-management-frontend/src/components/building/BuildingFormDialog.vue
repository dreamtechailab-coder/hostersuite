<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import { propertyService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { required, validate } from '@/utils/validation'
import type { Building } from '@/types'

const props = defineProps<{ building?: Building | null; property?: string }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [b: Building] }>()
const form = reactive<Partial<Building>>({})
const errors = ref<Record<string, string>>({})
watch(open, (o) => {
  if (!o) return
  errors.value = {}
  Object.assign(form, { name: undefined, property: props.property || '', building_name: '', is_active: 1, address_line: '', notes: '', ...(props.building || {}) })
})
const save = useMutation(propertyService.saveBuilding, { success: 'Building saved' })
async function submit() {
  errors.value = validate(form, { property: [required('Property')], building_name: [required('Building name')] })
  if (Object.keys(errors.value).length) return
  const res = await save.run(form)
  if (res) {
    emit('saved', res.data)
    open.value = false
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" :title="building?.name ? 'Edit building' : 'Add building'">
    <form id="building-form" class="space-y-4" @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property">
        <SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" :disabled="!!building?.name" />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Building name" required :error="errors.building_name">
        <Input :id="id" v-model="form.building_name" placeholder="e.g. Block A" :aria-invalid="invalid" />
      </FormField>
      <FormField v-slot="{ id }" label="Address (if different)"><Textarea :id="id" v-model="form.address_line" rows="2" /></FormField>
      <label class="flex items-center justify-between gap-3 text-sm font-medium">Active <Switch :model-value="!!form.is_active" @update:model-value="form.is_active = $event ? 1 : 0" /></label>
    </form>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="building-form" :loading="save.pending.value">Save</Button>
    </template>
  </ModalDialog>
</template>
