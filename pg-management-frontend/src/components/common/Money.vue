<script setup lang="ts">
import { computed } from 'vue'
import { formatCurrency } from '@/utils/currency'
const props = defineProps<{ value?: number | string | null; compact?: boolean; tone?: 'auto' | 'success' | 'danger' | 'muted' }>()
const text = computed(() => formatCurrency(props.value, { compact: props.compact }))
const cls = computed(() => {
  if (props.tone === 'success') return 'text-success'
  if (props.tone === 'danger') return Number(props.value) > 0 ? 'text-destructive' : 'text-muted-foreground'
  if (props.tone === 'muted') return 'text-muted-foreground'
  return ''
})
</script>
<template>
  <span :class="['tabular', cls]">{{ text }}</span>
</template>
