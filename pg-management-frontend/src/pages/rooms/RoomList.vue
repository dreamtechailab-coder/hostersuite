<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { LayoutGrid, List, Plus, DoorOpen } from 'lucide-vue-next'
import { useLocalStorage, watchDebounced } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import DataTable from '@/components/common/DataTable.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import RoomCard from '@/components/room/RoomCard.vue'
import RoomFormDialog from '@/components/room/RoomFormDialog.vue'
import { roomService } from '@/services/property.service'
import { useAsync } from '@/composables/useAsync'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const view = useLocalStorage<'grid' | 'table'>('pg.roomView', 'grid')
const { filters, activeCount, reset } = useFilters({ building: '', floor: '', status: '' })
const search = ref('')
const { data, loading, error, run } = useAsync(() =>
  roomService.board({ property: property.filter, building: filters.building || undefined, floor: filters.floor || undefined, status: filters.status || undefined, search: search.value || undefined }),
)
watch([() => property.filter, () => ({ ...filters })], () => run(), { immediate: true, deep: true })
watchDebounced(search, () => run(), { debounce: 300 })
const rooms = computed(() => data.value || [])
const addOpen = ref(false)
onMounted(() => {
  if (route.query.add) addOpen.value = true
})
const totals = computed(() => {
  const beds = rooms.value.reduce((a, r) => a + r.capacity, 0)
  const occ = rooms.value.reduce((a, r) => a + (r.occupied_beds || 0), 0)
  return { rooms: rooms.value.length, beds, vacant: rooms.value.reduce((a, r) => a + (r.beds || []).filter((b) => b.status === 'Vacant').length, 0), occ }
})
const columns = [
  { key: 'room_number', label: 'Room' },
  { key: 'building_name', label: 'Building' },
  { key: 'floor_name', label: 'Floor', mobileHidden: true },
  { key: 'room_type', label: 'Type' },
  { key: 'occupied_beds', label: 'Occupied', align: 'right' as const },
  { key: 'rent_per_bed', label: 'Rent / bed', format: 'currency' as const, align: 'right' as const },
  { key: 'status', label: 'Status', format: 'status' as const },
]
</script>

<template>
  <div>
    <PageHeader title="Rooms" :description="`${totals.rooms} rooms · ${totals.occ}/${totals.beds} beds occupied · ${totals.vacant} vacant`">
      <template #actions>
        <div class="flex rounded-lg border bg-card p-0.5" role="group" aria-label="View">
          <Button :variant="view === 'grid' ? 'secondary' : 'ghost'" size="icon-sm" aria-label="Grid view" :aria-pressed="view === 'grid'" @click="view = 'grid'"><LayoutGrid /></Button>
          <Button :variant="view === 'table' ? 'secondary' : 'ghost'" size="icon-sm" aria-label="Table view" :aria-pressed="view === 'table'" @click="view = 'table'"><List /></Button>
        </div>
        <Button v-if="can('PG Room', 'create')" @click="addOpen = true"><Plus />Add room</Button>
      </template>
    </PageHeader>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="search" placeholder="Room number…" class="sm:w-48" /></template>
        <SearchSelect v-model="filters.building" doctype="PG Building" :filters="property.filter ? { property: property.filter } : undefined" placeholder="All buildings" class="lg:w-48" />
        <SearchSelect v-model="filters.floor" doctype="PG Floor" :filters="filters.building ? { building: filters.building } : property.filter ? { property: property.filter } : undefined" placeholder="All floors" class="lg:w-44" />
        <NativeSelect v-model="filters.status" :options="['Available', 'Full', 'Maintenance']" placeholder="Any status" class="lg:w-40" />
      </FilterPanel>
    </div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else-if="view === 'grid'">
      <LoadingSkeleton v-if="loading && !rooms.length" variant="cards" />
      <EmptyState v-else-if="!rooms.length" :icon="DoorOpen" title="No rooms match" description="Add rooms to a floor to start allocating beds.">
        <Button v-if="can('PG Room', 'create')" @click="addOpen = true"><Plus />Add room</Button>
      </EmptyState>
      <div v-else :class="['grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4', loading && 'opacity-60']">
        <RoomCard v-for="r in rooms" :key="r.name" :room="r" />
      </div>
    </template>
    <DataTable v-else :columns="columns" :rows="rooms" :loading="loading" clickable @row-click="(r) => router.push(`/rooms/${r.name}`)">
      <template #cell-occupied_beds="{ row }"><span class="tabular">{{ row.occupied_beds || 0 }}/{{ row.capacity }}</span></template>
    </DataTable>
    <RoomFormDialog v-model:open="addOpen" :defaults="{ property: property.filter || '', building: (route.query.building as string) || '', floor: (route.query.floor as string) || '' }" @saved="run" />
  </div>
</template>
