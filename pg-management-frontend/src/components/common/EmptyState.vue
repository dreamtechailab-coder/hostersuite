<script setup lang="ts">
import type { Component } from 'vue'
import { Inbox } from 'lucide-vue-next'

withDefaults(defineProps<{ title?: string; description?: string; icon?: Component; compact?: boolean }>(), {
  title: 'Nothing here yet',
})
</script>

<template>
  <div :class="['flex flex-col items-center justify-center text-center', compact ? 'px-4 py-8' : 'px-6 py-14']">
    <div class="mb-3 flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
      <component :is="icon || Inbox" class="size-5" />
    </div>
    <p class="font-medium">{{ title }}</p>
    <p v-if="description" class="mt-1 max-w-sm text-sm text-muted-foreground">{{ description }}</p>
    <div v-if="$slots.default" class="mt-4 flex flex-wrap justify-center gap-2"><slot /></div>
  </div>
</template>
