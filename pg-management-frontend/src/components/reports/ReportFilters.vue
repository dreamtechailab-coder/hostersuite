<script setup lang="ts">
import { Download } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import DateRangePicker, { type Preset } from '@/components/common/DateRangePicker.vue'

const range = defineModel<{ from: string; to: string }>('range', { required: true })
const preset = defineModel<Preset>('preset', { default: 'last_12' })
defineProps<{ canExport?: boolean }>()
const emit = defineEmits<{ export: [] }>()
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <DateRangePicker v-model="range" v-model:preset="preset" />
    <Button variant="outline" :disabled="!canExport" @click="emit('export')"><Download />Export CSV</Button>
  </div>
</template>
