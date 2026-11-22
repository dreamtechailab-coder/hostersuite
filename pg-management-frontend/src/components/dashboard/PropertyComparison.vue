<script setup lang="ts">
import { RouterLink } from 'vue-router'
import Money from '@/components/common/Money.vue'
import EmptyState from '@/components/common/EmptyState.vue'

defineProps<{ rows: { property: string; property_name: string; beds: number; occupied: number; vacant: number; collected?: number }[]; showRevenue?: boolean }>()
const rate = (r: { beds: number; occupied: number }) => (r.beds ? Math.round((r.occupied / r.beds) * 100) : 0)
</script>

<template>
  <EmptyState v-if="!rows.length" compact title="No properties yet" />
  <ul v-else class="divide-y">
    <li v-for="r in rows" :key="r.property">
      <RouterLink :to="`/properties/${encodeURIComponent(r.property)}`" class="block py-3 hover:bg-muted/40 -mx-2 px-2 rounded-lg">
        <div class="flex items-baseline justify-between gap-3">
          <p class="truncate text-sm font-medium">{{ r.property_name }}</p>
          <p class="tabular shrink-0 text-sm font-semibold">{{ rate(r) }}%</p>
        </div>
        <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
          <div class="h-full rounded-full bg-primary" :style="{ width: `${rate(r)}%` }" />
        </div>
        <div class="mt-1.5 flex justify-between text-xs text-muted-foreground">
          <span class="tabular">{{ r.occupied }}/{{ r.beds }} beds · {{ r.vacant }} vacant</span>
          <span v-if="showRevenue"><Money :value="r.collected" /> collected</span>
        </div>
      </RouterLink>
    </li>
  </ul>
</template>
