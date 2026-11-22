<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import { rentService } from '@/services/rent.service'
import { useMutation } from '@/composables/useMutation'
import { usePropertyStore } from '@/stores/property'
import { useDashboardStore } from '@/stores/dashboard'

const props = defineProps<{ month?: string }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ done: [] }>()
const property = usePropertyStore()
const dashboard = useDashboardStore()
const month = ref('')
const result = ref<{ created: string[]; skipped: number; errors: { occupancy: string; error: string }[] } | null>(null)
watch(open, (o) => {
  if (o) {
    month.value = (props.month || new Date().toISOString()).slice(0, 7)
    result.value = null
  }
})
const gen = useMutation((m: string) => rentService.generate(`${m}-01`, property.filter))
async function submit() {
  const res = await gen.run(month.value)
  if (res) {
    result.value = res.data
    dashboard.invalidate()
    emit('done')
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" title="Generate rent invoices" :description="`For ${property.label}. Includes pro-rated rent, unbilled electricity and late fees. Already-invoiced tenants are skipped.`">
    <div v-if="!result" class="space-y-4">
      <FormField v-slot="{ id }" label="Billing month"><Input :id="id" v-model="month" type="month" /></FormField>
    </div>
    <div v-else class="space-y-3 text-sm">
      <p><strong class="tabular">{{ result.created.length }}</strong> invoice(s) created, <span class="tabular">{{ result.skipped }}</span> skipped (nothing to bill).</p>
      <div v-if="result.errors.length" class="rounded-lg bg-danger-soft p-3 text-destructive">
        <p class="font-medium">{{ result.errors.length }} could not be generated:</p>
        <ul class="mt-1 list-disc pl-5"><li v-for="e in result.errors" :key="e.occupancy">{{ e.occupancy }}: {{ e.error }}</li></ul>
      </div>
    </div>
    <template #footer>
      <Button variant="outline" @click="open = false">{{ result ? 'Close' : 'Cancel' }}</Button>
      <Button v-if="!result" :loading="gen.pending.value" :disabled="!month" @click="submit">Generate</Button>
    </template>
  </ModalDialog>
</template>
