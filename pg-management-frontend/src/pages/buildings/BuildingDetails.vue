<script setup lang="ts">
import { computed, ref } from 'vue'
import { Layers, Plus, Pencil } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import RoomCard from '@/components/room/RoomCard.vue'
import FloorFormDialog from '@/components/floor/FloorFormDialog.vue'
import BuildingFormDialog from '@/components/building/BuildingFormDialog.vue'
import { resource } from '@/services/resource.service'
import { roomService } from '@/services/property.service'
import { useAsync } from '@/composables/useAsync'
import { usePermissions } from '@/composables/usePermissions'
import type { Building, Floor, Room } from '@/types'

const props = defineProps<{ name: string }>()
const { can } = usePermissions()
const { data, loading, error, run } = useAsync(async () => {
  const b = (await resource.get<Building>('PG Building', props.name)).data
  const [floors, rooms] = await Promise.all([
    resource.list<Floor>('PG Floor', { filters: { building: props.name }, page_size: 100, order_by: 'floor_number asc' }),
    roomService.board({ property: b.property, building: props.name }),
  ])
  return { building: b, floors: floors.data, rooms }
}, { immediate: true })
const byFloor = computed(() => (data.value?.floors || []).map((f) => ({ ...f, rooms: (data.value?.rooms || []).filter((r: Room) => r.floor === f.name) })))
const floorOpen = ref(false)
const editOpen = ref(false)
</script>

<template>
  <div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data">
      <PageHeader :title="data.building.building_name" :description="data.building.property" back="/buildings">
        <template #actions>
          <Button v-if="can('PG Building', 'write')" variant="outline" @click="editOpen = true"><Pencil />Edit</Button>
          <Button v-if="can('PG Floor', 'create')" @click="floorOpen = true"><Plus />Floor</Button>
        </template>
      </PageHeader>
      <EmptyState v-if="!byFloor.length" :icon="Layers" title="No floors in this building" />
      <section v-for="f in byFloor" :key="f.name" class="mb-6">
        <div class="mb-3 flex items-center gap-2">
          <Layers class="size-4 text-muted-foreground" />
          <h2 class="font-semibold">{{ f.floor_name }}</h2>
          <span class="text-sm text-muted-foreground">· {{ f.rooms.length }} rooms</span>
        </div>
        <Card v-if="!f.rooms.length"><CardContent class="text-sm text-muted-foreground">No rooms on this floor. <RouterLink :to="{ path: '/rooms', query: { add: '1', building: name, floor: f.name } }" class="font-medium text-primary hover:underline">Add a room</RouterLink></CardContent></Card>
        <div v-else class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><RoomCard v-for="r in f.rooms" :key="r.name" :room="r" /></div>
      </section>
      <FloorFormDialog v-model:open="floorOpen" :property="data.building.property" :building="name" @saved="run" />
      <BuildingFormDialog v-model:open="editOpen" :building="data.building" @saved="run" />
    </template>
  </div>
</template>
