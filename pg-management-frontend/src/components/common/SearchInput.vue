<script setup lang="ts">
import { Search, X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import type { HTMLAttributes } from 'vue'

const props = withDefaults(defineProps<{ placeholder?: string; class?: HTMLAttributes['class'] }>(), { placeholder: 'Search…' })
const model = defineModel<string>({ default: '' })
</script>

<template>
  <div :class="cn('relative w-full sm:w-72', props.class)">
    <Search class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
    <input
      v-model="model"
      type="search"
      :placeholder="placeholder"
      :aria-label="placeholder"
      class="h-10 w-full rounded-lg border border-input bg-card pl-9 pr-9 text-base shadow-xs outline-none placeholder:text-muted-foreground/70 focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/25 md:text-sm [&::-webkit-search-cancel-button]:hidden"
    />
    <button
      v-if="model"
      type="button"
      class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
      aria-label="Clear search"
      @click="model = ''"
    >
      <X class="size-4" />
    </button>
  </div>
</template>
