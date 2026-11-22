<script setup lang="ts">
import { computed } from 'vue'
import { BedDouble, BedSingle, Wrench, Clock } from 'lucide-vue-next'
import type { Bed } from '@/types'

const props = defineProps<{ bed: Bed; interactive?: boolean; compact?: boolean }>()
defineEmits<{ select: [bed: Bed] }>()
const meta = computed(
  () =>
    ({
      Vacant: { cls: 'border-success/30 bg-success-soft text-success hover:border-success', icon: BedSingle, text: 'Vacant' },
      Occupied: { cls: 'border-primary/20 bg-primary/5 text-primary', icon: BedDouble, text: props.bed.tenant_name || 'Occupied' },
      Reserved: { cls: 'border-info/30 bg-info-soft text-info', icon: Clock, text: props.bed.reserved_for ? `Held · ${props.bed.reserved_for}` : 'Reserved' },
      Maintenance: { cls: 'border-warning/30 bg-warning-soft text-warning', icon: Wrench, text: 'Maintenance' },
    })[props.bed.status],
)
</script>

<template>
  <component
    :is="interactive ? 'button' : 'div'"
    type="button"
    :class="[
      'flex min-w-0 items-center gap-2 rounded-lg border text-left transition',
      compact ? 'px-2 py-1.5' : 'px-3 py-2.5',
      meta.cls,
      interactive && 'cursor-pointer focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40',
    ]"
    :aria-label="`Bed ${bed.bed_label}: ${meta.text}`"
    @click="interactive && $emit('select', bed)"
  >
    <component :is="meta.icon" class="size-4 shrink-0" />
    <span class="min-w-0">
      <span class="block text-xs font-semibold">Bed {{ bed.bed_label }}</span>
      <span v-if="!compact" class="block truncate text-[11px] text-foreground/70">{{ meta.text }}</span>
    </span>
  </component>
</template>
