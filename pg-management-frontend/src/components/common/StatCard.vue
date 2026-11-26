<script setup lang="ts">
import type { Component } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    label: string
    value?: string | number
    hint?: string
    icon?: Component
    tone?: 'default' | 'success' | 'danger' | 'warning' | 'info'
    loading?: boolean
    to?: RouteLocationRaw
    progress?: number
  }>(),
  { tone: 'default' },
)
const toneClass = {
  default: 'bg-primary/10 text-primary',
  success: 'bg-success-soft text-success',
  danger: 'bg-danger-soft text-destructive',
  warning: 'bg-warning-soft text-warning',
  info: 'bg-info-soft text-info',
}
const barClass = { default: 'bg-primary', success: 'bg-success', danger: 'bg-destructive', warning: 'bg-warning', info: 'bg-info' }
</script>

<template>
  <component
    :is="to ? RouterLink : 'div'"
    :to="to"
    :class="
      cn(
        'group flex flex-col gap-3 rounded-xl border bg-card p-4 shadow-xs transition sm:p-5',
        to && 'hover:border-primary/30 hover:shadow-sm focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40',
      )
    "
  >
    <div class="flex items-start justify-between gap-2">
      <p class="text-[13px] font-medium text-muted-foreground">{{ label }}</p>
      <span v-if="icon" :class="cn('flex size-8 shrink-0 items-center justify-center rounded-lg', toneClass[props.tone])">
        <component :is="icon" class="size-4" />
      </span>
    </div>
    <div>
      <Skeleton v-if="loading" class="h-7 w-24" />
      <p v-else class="tabular text-xl font-semibold tracking-tight [overflow-wrap:anywhere] sm:text-2xl">{{ value ?? '—' }}</p>
      <p v-if="hint && !loading" class="mt-1 truncate text-xs text-muted-foreground">{{ hint }}</p>
      <slot />
    </div>
    <div v-if="progress !== undefined && !loading" class="h-1.5 overflow-hidden rounded-full bg-muted" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
      <div :class="cn('h-full rounded-full transition-all', barClass[props.tone])" :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }" />
    </div>
  </component>
</template>
