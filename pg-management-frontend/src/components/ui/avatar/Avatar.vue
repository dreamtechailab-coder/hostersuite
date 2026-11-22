<script setup lang="ts">
import { computed, type HTMLAttributes } from 'vue'
import { AvatarFallback, AvatarImage, AvatarRoot } from 'reka-ui'
import { cn } from '@/lib/utils'
const props = defineProps<{ name?: string | null; src?: string | null; class?: HTMLAttributes['class'] }>()
const initials = computed(() =>
  (props.name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join(''),
)
</script>
<template>
  <AvatarRoot :class="cn('relative flex size-9 shrink-0 overflow-hidden rounded-full bg-primary/10', props.class)">
    <AvatarImage v-if="src" :src="src" :alt="name || ''" class="aspect-square size-full object-cover" />
    <AvatarFallback class="flex size-full items-center justify-center text-xs font-semibold text-primary">{{ initials }}</AvatarFallback>
  </AvatarRoot>
</template>
