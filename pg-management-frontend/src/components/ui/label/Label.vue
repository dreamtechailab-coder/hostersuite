<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Label, type LabelProps } from 'reka-ui'
import { cn } from '@/lib/utils'

const props = defineProps<LabelProps & { class?: HTMLAttributes['class'] }>()
</script>

<template>
  <Label
    :for="props.for"
    :class="cn('flex items-center gap-1 text-sm font-medium leading-none select-none peer-disabled:opacity-50', props.class)"
  >
    <slot />
  </Label>
</template>
