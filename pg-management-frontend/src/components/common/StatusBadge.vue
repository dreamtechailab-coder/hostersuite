<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import type { BadgeVariants } from '@/components/ui/badge'

/** One consistent status → colour mapping for the whole app. */
const MAP: Record<string, BadgeVariants['variant']> = {
  // money
  Paid: 'success',
  Unpaid: 'warning',
  'Partially Paid': 'info',
  Overdue: 'danger',
  Draft: 'neutral',
  Cancelled: 'neutral',
  Billed: 'success',
  Unbilled: 'warning',
  'Partially Billed': 'info',
  Refunded: 'success',
  Held: 'info',
  Adjusted: 'neutral',
  // occupancy
  Active: 'success',
  'On Notice': 'warning',
  Ended: 'neutral',
  Vacated: 'neutral',
  Prospective: 'info',
  Vacant: 'success',
  Occupied: 'default',
  Reserved: 'info',
  Maintenance: 'warning',
  Available: 'success',
  Full: 'default',
  // bookings
  Pending: 'warning',
  Confirmed: 'info',
  'Checked In': 'success',
  // messages
  Sent: 'success',
  Queued: 'info',
  Failed: 'danger',
  Enabled: 'success',
  Disabled: 'neutral',
}
const props = defineProps<{ status?: string | null; dot?: boolean }>()
const variant = computed(() => MAP[props.status || ''] ?? 'neutral')
</script>

<template>
  <Badge v-if="status" :variant="variant">
    <span v-if="dot !== false" class="size-1.5 rounded-full bg-current" aria-hidden="true" />
    {{ status }}
  </Badge>
</template>
