<script setup lang="ts">
import { SlidersHorizontal } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

/**
 * Filter container: inline on desktop, a popover button on mobile so the list
 * stays visible. Pass filter controls in the default slot.
 */
defineProps<{ activeCount?: number }>()
const emit = defineEmits<{ reset: [] }>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <slot name="search" />
    <div class="hidden flex-wrap items-center gap-2 lg:flex">
      <slot />
      <Button v-if="activeCount" variant="ghost" size="sm" @click="emit('reset')">Clear</Button>
    </div>
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="outline" class="lg:hidden" aria-label="Filters">
          <SlidersHorizontal />
          Filters
          <span v-if="activeCount" class="ml-0.5 rounded-full bg-primary px-1.5 text-[11px] text-primary-foreground">{{ activeCount }}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" class="w-[min(20rem,calc(100vw-2rem))]">
        <div class="flex flex-col gap-3 [&>*]:w-full"><slot /></div>
        <Button v-if="activeCount" variant="ghost" size="sm" class="mt-2 w-full" @click="emit('reset')">Clear filters</Button>
      </PopoverContent>
    </Popover>
  </div>
</template>
