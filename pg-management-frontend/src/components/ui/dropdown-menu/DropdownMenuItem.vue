<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { DropdownMenuItem } from 'reka-ui'
import { cn } from '@/lib/utils'
const props = defineProps<{ class?: HTMLAttributes['class']; destructive?: boolean; disabled?: boolean }>()
const emit = defineEmits<{ select: [e: Event] }>()
</script>
<template>
  <DropdownMenuItem
    :disabled="disabled"
    :class="
      cn(
        'relative flex min-h-9 cursor-default select-none items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:size-4 [&_svg]:text-muted-foreground',
        destructive && 'text-destructive data-[highlighted]:bg-danger-soft data-[highlighted]:text-destructive [&_svg]:text-destructive',
        props.class,
      )
    "
    @select="emit('select', $event)"
  >
    <slot />
  </DropdownMenuItem>
</template>
