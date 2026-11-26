<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { Building2, MapPin } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import type { Property } from '@/types'

const props = defineProps<{ property: Property }>()
const rate = computed(() => (props.property.total_beds ? Math.round(((props.property.occupied_beds || 0) / props.property.total_beds) * 100) : 0))
</script>

<template>
  <RouterLink
    :to="`/properties/${encodeURIComponent(property.name)}`"
    class="group flex min-w-0 flex-col rounded-xl border bg-card p-4 shadow-xs sm:p-5 transition hover:border-primary/30 hover:shadow-sm focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40"
  >
    <div class="flex items-start gap-3">
      <span class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><Building2 class="size-5" /></span>
      <div class="min-w-0 flex-1">
        <p class="truncate font-semibold group-hover:text-primary">{{ property.property_name }}</p>
        <p class="mt-0.5 flex items-center gap-1 truncate text-sm text-muted-foreground"><MapPin class="size-3.5" />{{ property.city || 'No city' }}</p>
      </div>
      <Badge :variant="property.is_active ? 'neutral' : 'warning'">{{ property.is_active ? property.property_type : 'Inactive' }}</Badge>
    </div>
    <div class="mt-5">
      <div class="flex items-baseline justify-between text-sm">
        <span class="text-muted-foreground">Occupancy</span>
        <span class="tabular font-semibold">{{ rate }}%</span>
      </div>
      <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"><div class="h-full rounded-full bg-primary" :style="{ width: `${rate}%` }" /></div>
      <p class="tabular mt-2 text-xs text-muted-foreground">{{ property.occupied_beds || 0 }} of {{ property.total_beds || 0 }} beds occupied</p>
    </div>
  </RouterLink>
</template>
