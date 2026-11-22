<script setup lang="ts">
import { Skeleton } from '@/components/ui/skeleton'
withDefaults(defineProps<{ variant?: 'table' | 'cards' | 'detail' | 'stats' | 'form'; rows?: number }>(), { variant: 'table', rows: 6 })
</script>

<template>
  <div aria-busy="true" aria-label="Loading">
    <div v-if="variant === 'stats'" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="rounded-xl border bg-card p-5"><Skeleton class="mb-4 h-4 w-24" /><Skeleton class="h-7 w-28" /></div>
    </div>
    <div v-else-if="variant === 'cards'" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="i in rows" :key="i" class="rounded-xl border bg-card p-5">
        <Skeleton class="mb-3 h-5 w-1/2" /><Skeleton class="mb-2 h-4 w-3/4" /><Skeleton class="h-4 w-1/3" />
      </div>
    </div>
    <div v-else-if="variant === 'detail'" class="space-y-4">
      <div class="rounded-xl border bg-card p-5"><Skeleton class="mb-4 h-6 w-48" /><div class="grid gap-4 sm:grid-cols-3"><Skeleton v-for="i in 6" :key="i" class="h-10" /></div></div>
      <div class="rounded-xl border bg-card p-5"><Skeleton v-for="i in 4" :key="i" class="mb-3 h-10" /></div>
    </div>
    <div v-else-if="variant === 'form'" class="space-y-5 rounded-xl border bg-card p-5">
      <div v-for="i in rows" :key="i"><Skeleton class="mb-2 h-4 w-28" /><Skeleton class="h-10" /></div>
    </div>
    <div v-else class="divide-y">
      <div v-for="i in rows" :key="i" class="flex items-center gap-4 px-4 py-3.5">
        <Skeleton class="size-8 rounded-full" /><Skeleton class="h-4 flex-1" /><Skeleton class="hidden h-4 w-24 sm:block" /><Skeleton class="h-4 w-16" />
      </div>
    </div>
  </div>
</template>
