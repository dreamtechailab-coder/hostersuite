<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BedSingle } from 'lucide-vue-next'
import { Switch } from '@/components/ui/switch'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import RoomCard from '@/components/room/RoomCard.vue'
import CheckInDialog from '@/components/occupancy/CheckInDialog.vue'
import { roomService } from '@/services/property.service'
import { useAsync } from '@/composables/useAsync'
import { useFilters } from '@/composables/useFilters'
import { usePropertyStore } from '@/stores/property'
import type { Bed, Room } from '@/types'

/** Visual board: pick a vacant bed to check a tenant in (optionally for a booking). */
const route = useRoute()
const property = usePropertyStore()
const { filters, activeCount, reset } = useFilters({ building: '', vacant: '1' })
const { data, loading, error, run } = useAsync(() =>
  roomService.board({ property: property.filter, building: filters.building || undefined, vacant_only: filters.vacant === '1' ? 1 : 0 }),
)
watch([() => property.filter, () => ({ ...filters })], () => run(), { immediate: true, deep: true })
const rooms = computed(() => data.value || [])
const vacant = computed(() => rooms.value.reduce((a, r) => a + (r.beds || []).filter((b) => b.status === 'Vacant').length, 0))

const open = ref(false)
const bed = ref('')
const room = ref<Room | null>(null)
const tenant = computed(() => (route.query.tenant as string) || '')
const booking = computed(() => (route.query.booking as string) || '')
function select(b: Bed, r: Room) {
  bed.value = b.name
  room.value = r
  open.value = true
}
</script>

<template>
  <div>
    <PageHeader title="Bed allocation" :description="booking ? `Choose a bed for booking ${booking}` : `${vacant} vacant beds – tap one to check a tenant in.`" />
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <SearchSelect v-model="filters.building" doctype="PG Building" :filters="property.filter ? { property: property.filter } : undefined" placeholder="All buildings" class="lg:w-56" />
        <label class="flex h-10 items-center gap-2 rounded-lg border bg-card px-3 text-sm">
          <Switch :model-value="filters.vacant === '1'" @update:model-value="filters.vacant = $event ? '1' : '0'" />Only rooms with vacancies
        </label>
      </FilterPanel>
    </div>
    <div class="mb-4 flex flex-wrap gap-4 text-xs text-muted-foreground" aria-label="Legend">
      <span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-success" />Vacant (tap to allocate)</span>
      <span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-primary" />Occupied</span>
      <span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-info" />Reserved</span>
      <span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-sm bg-warning" />Maintenance</span>
    </div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !rooms.length" variant="cards" />
    <EmptyState v-else-if="!rooms.length" :icon="BedSingle" title="No vacant beds" description="All beds are occupied or reserved for the current filters." />
    <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
      <RoomCard v-for="r in rooms" :key="r.name" :room="r" selectable @select-bed="select" />
    </div>
    <CheckInDialog v-model:open="open" :bed="bed" :room="room" :tenant="tenant" :booking="booking || undefined" @done="run" />
  </div>
</template>
