<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import { electricityService } from '@/services/rent.service'
import { useMutation } from '@/composables/useMutation'
import { formatCurrency, formatNumber } from '@/utils/currency'
import { addDays, monthStart, today } from '@/utils/date'
import type { Meter, MeterReading } from '@/types'

const props = defineProps<{ meter: Meter | null }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()
const form = reactive({ current_reading: null as number | null, reading_date: today(), period_start: '', period_end: today() })
const preview = ref<MeterReading | null>(null)
const previewError = ref('')
watch(open, (o) => {
  if (!o || !props.meter) return
  preview.value = null
  previewError.value = ''
  Object.assign(form, {
    current_reading: null,
    reading_date: today(),
    period_start: props.meter.last_reading_date ? addDays(props.meter.last_reading_date, 1) : monthStart(),
    period_end: today(),
  })
})
const invalid = computed(() => form.current_reading === null || Number(form.current_reading) < Number(props.meter?.last_reading || 0))
watchDebounced(
  () => [form.current_reading, form.period_start, form.period_end],
  async () => {
    preview.value = null
    previewError.value = ''
    if (!props.meter || invalid.value || !form.period_start) return
    try {
      preview.value = await electricityService.preview({ meter: props.meter.name, current_reading: Number(form.current_reading), reading_date: form.reading_date, period_start: form.period_start, period_end: form.period_end })
    } catch (e) {
      previewError.value = (e as Error).message
    }
  },
  { debounce: 400 },
)
const save = useMutation(() => electricityService.record({ meter: props.meter!.name, current_reading: Number(form.current_reading), reading_date: form.reading_date, period_start: form.period_start, period_end: form.period_end }))
async function submit() {
  if (invalid.value) return
  if (await save.run()) {
    emit('saved')
    open.value = false
  }
}
</script>

<template>
  <ModalDialog v-model:open="open" :title="`Record reading · Meter ${meter?.meter_number}`" :description="`Room ${meter?.room_number} · last reading ${formatNumber(meter?.last_reading, 2)}`">
    <form id="reading-form" class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
      <FormField v-slot="{ id }" label="Current reading" required :error="form.current_reading !== null && invalid ? `Must be at least ${meter?.last_reading}` : ''" class="sm:col-span-2">
        <Input :id="id" v-model.number="form.current_reading" type="number" step="0.01" :min="meter?.last_reading" inputmode="decimal" autofocus class="h-12 text-lg" />
      </FormField>
      <FormField v-slot="{ id }" label="Period from"><Input :id="id" v-model="form.period_start" type="date" /></FormField>
      <FormField v-slot="{ id }" label="Period to"><Input :id="id" v-model="form.period_end" type="date" :min="form.period_start" /></FormField>
    </form>
    <div v-if="previewError" class="mt-4 rounded-lg bg-danger-soft p-3 text-sm text-destructive">{{ previewError }}</div>
    <div v-if="preview" class="mt-4 rounded-lg border bg-muted/30 p-4 text-sm">
      <div class="flex justify-between"><span class="text-muted-foreground">Units consumed</span><span class="tabular font-medium">{{ formatNumber(preview.units_consumed, 2) }}</span></div>
      <div class="mt-1 flex justify-between"><span class="text-muted-foreground">Bill @ {{ formatCurrency(preview.rate_per_unit) }}/unit</span><span class="tabular font-semibold">{{ formatCurrency(preview.amount) }}</span></div>
      <p class="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">Split among occupants (by days stayed)</p>
      <p v-if="!preview.shares?.length" class="mt-1 text-muted-foreground">Room was vacant – nothing will be billed to tenants.</p>
      <ul class="mt-1 divide-y">
        <li v-for="s in preview.shares" :key="s.tenant" class="flex justify-between py-1.5"><span>{{ s.tenant_name }} <span class="text-muted-foreground">· {{ s.days }} days</span></span><span class="tabular">{{ formatCurrency(s.amount) }}</span></li>
      </ul>
    </div>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button type="submit" form="reading-form" :disabled="invalid" :loading="save.pending.value">Save reading</Button>
    </template>
  </ModalDialog>
</template>
