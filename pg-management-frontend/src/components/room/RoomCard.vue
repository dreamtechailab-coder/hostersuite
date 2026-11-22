<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Snowflake, Bath } from 'lucide-vue-next'
import StatusBadge from '@/components/common/StatusBadge.vue'
import BedCard from './BedCard.vue'
import { formatCurrency } from '@/utils/currency'
import type { Bed, Room } from '@/types'

defineProps<{ room: Room; selectable?: boolean }>()
const emit = defineEmits<{ 'select-bed': [bed: Bed, room: Room] }>()
</script>

<template>
  <div class="flex flex-col rounded-xl border bg-card p-4 shadow-xs">
    <div class="flex items-start justify-between gap-2">
      <RouterLink :to="`/rooms/${room.name}`" class="min-w-0 hover:underline">
        <p class="font-semibold">Room {{ room.room_number }}</p>
        <p class="truncate text-xs text-muted-foreground">{{ [room.building_name, room.floor_name].filter(Boolean).join(' · ') || room.room_type }}</p>
      </RouterLink>
      <StatusBadge :status="room.status" />
    </div>
    <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
      <span>{{ room.room_type }}</span>
      <span class="tabular">{{ formatCurrency(room.rent_per_bed) }}/bed</span>
      <span v-if="room.is_ac" class="inline-flex items-center gap-0.5"><Snowflake class="size-3" />AC</span>
      <span v-if="room.attached_bathroom" class="inline-flex items-center gap-0.5"><Bath class="size-3" />Attached</span>
    </div>
    <div v-if="room.beds?.length" class="mt-3 grid grid-cols-2 gap-1.5">
      <BedCard
        v-for="b in room.beds"
        :key="b.name"
        :bed="b"
        compact
        :interactive="selectable && b.status === 'Vacant'"
        @select="emit('select-bed', $event, room)"
      />
    </div>
    <p class="tabular mt-3 text-xs text-muted-foreground">{{ room.occupied_beds || 0 }}/{{ room.capacity }} occupied</p>
  </div>
</template>
