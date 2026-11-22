<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { CheckboxIndicator, CheckboxRoot } from 'reka-ui'
import { Check } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
const props = defineProps<{ class?: HTMLAttributes['class']; disabled?: boolean; id?: string }>()
const model = defineModel<boolean>({ default: false })
</script>
<template>
  <CheckboxRoot
    :id="id"
    v-model="model"
    :disabled="disabled"
    :class="
      cn(
        'peer size-5 shrink-0 rounded-[5px] border border-input bg-card shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40 disabled:opacity-50 data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground',
        props.class,
      )
    "
  >
    <CheckboxIndicator class="flex items-center justify-center"><Check class="size-3.5" /></CheckboxIndicator>
  </CheckboxRoot>
</template>
