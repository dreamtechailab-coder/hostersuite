<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import type { SelectOption } from '.'

defineOptions({ inheritAttrs: false })
const props = defineProps<{
  options: (SelectOption | string)[]
  placeholder?: string
  class?: HTMLAttributes['class']
}>()
const model = defineModel<string | number | null | undefined>()
const norm = (o: SelectOption | string): SelectOption => (typeof o === 'string' ? { value: o, label: o } : o)
</script>

<template>
  <div :class="cn('relative', props.class)">
    <select
      v-model="model"
      v-bind="$attrs"
      :class="
        cn(
          'h-10 w-full appearance-none rounded-lg border border-input bg-card pl-3 pr-9 text-base shadow-xs outline-none md:text-sm',
          'focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/25 disabled:opacity-50 aria-invalid:border-destructive',
          (model === '' || model == null) && 'text-muted-foreground',
        )
      "
    >
      <option v-if="placeholder !== undefined" value="">{{ placeholder }}</option>
      <option v-for="o in options.map(norm)" :key="o.value" :value="o.value" :disabled="o.disabled" class="text-foreground">
        {{ o.label }}
      </option>
    </select>
    <ChevronDown class="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
  </div>
</template>
