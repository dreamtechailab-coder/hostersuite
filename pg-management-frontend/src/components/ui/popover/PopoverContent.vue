<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { PopoverContent, PopoverPortal } from 'reka-ui'
import { cn } from '@/lib/utils'
const props = withDefaults(
  defineProps<{ class?: HTMLAttributes['class']; align?: 'start' | 'center' | 'end'; sideOffset?: number }>(),
  { align: 'start', sideOffset: 6 },
)
</script>
<template>
  <PopoverPortal>
    <PopoverContent
      :align="align"
      :side-offset="sideOffset"
      :class="
        cn(
          'z-50 w-72 rounded-lg border bg-popover p-3 text-popover-foreground shadow-lg outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
          props.class,
        )
      "
    >
      <slot />
    </PopoverContent>
  </PopoverPortal>
</template>
