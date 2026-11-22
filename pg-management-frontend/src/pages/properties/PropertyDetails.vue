<script setup lang="ts">
import { ref } from 'vue'
import { Building, DoorOpen, Layers, Pencil, Plus, Users, BedDouble, MapPin, Phone } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BuildingFormDialog from '@/components/building/BuildingFormDialog.vue'
import FloorFormDialog from '@/components/floor/FloorFormDialog.vue'
import { propertyService } from '@/services/property.service'
import { useAsync } from '@/composables/useAsync'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { formatPercent } from '@/utils/currency'

const props = defineProps<{ name: string }>()
const { can } = usePermissions()
const propertyStore = usePropertyStore()
const { data, loading, error, run } = useAsync(() => propertyService.overview(props.name), { immediate: true })
const buildingOpen = ref(false)
const floorOpen = ref(false)
const floorBuilding = ref('')
const total = (b: Record<string, number>) => Object.values(b).reduce((a, c) => a + c, 0)
function addFloor(building: string) {
  floorBuilding.value = building
  floorOpen.value = true
}
</script>

<template>
  <div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data">
      <PageHeader :title="data.property.property_name" back="/properties">
        <template #badge>
          <Badge variant="neutral">{{ data.property.property_type }}</Badge>
          <Badge v-if="!data.property.is_active" variant="warning">Inactive</Badge>
        </template>
        <template #description>
          <span class="inline-flex flex-wrap items-center gap-x-4 gap-y-1">
            <span v-if="data.property.city" class="inline-flex items-center gap-1"><MapPin class="size-3.5" />{{ [data.property.address_line, data.property.city].filter(Boolean).join(', ') }}</span>
            <a v-if="data.property.phone" :href="`tel:${data.property.phone}`" class="inline-flex items-center gap-1 hover:text-foreground"><Phone class="size-3.5" />{{ data.property.phone }}</a>
          </span>
        </template>
        <template #actions>
          <Button variant="outline" @click="propertyStore.select(name)">Set as current</Button>
          <Button v-if="can('PG Property', 'write')" variant="outline" as-child><RouterLink :to="`/properties/${encodeURIComponent(name)}/edit`"><Pencil />Edit</RouterLink></Button>
          <Button v-if="can('PG Building', 'create')" @click="buildingOpen = true"><Plus />Building</Button>
        </template>
      </PageHeader>

      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Occupancy" :value="formatPercent(total(data.beds) ? ((data.beds.Occupied || 0) * 100) / total(data.beds) : 0)" :icon="BedDouble" :progress="total(data.beds) ? ((data.beds.Occupied || 0) * 100) / total(data.beds) : 0" />
        <StatCard label="Beds" :value="total(data.beds)" :hint="`${data.beds.Vacant || 0} vacant · ${data.beds.Reserved || 0} reserved`" :icon="DoorOpen" tone="info" />
        <StatCard label="Active tenants" :value="data.active_tenants" :icon="Users" tone="success" :to="`/occupancy?property=${encodeURIComponent(name)}`" />
        <StatCard label="Buildings" :value="data.buildings.length" :hint="`${data.buildings.reduce((a, b) => a + b.floors.length, 0)} floors`" :icon="Building" />
      </div>

      <h2 class="mb-3 mt-8 text-base font-semibold">Buildings & floors</h2>
      <EmptyState v-if="!data.buildings.length" :icon="Building" title="No buildings yet" description="Add a building, then floors and rooms inside it.">
        <Button v-if="can('PG Building', 'create')" @click="buildingOpen = true"><Plus />Add building</Button>
      </EmptyState>
      <div class="grid gap-4 lg:grid-cols-2">
        <Card v-for="b in data.buildings" :key="b.name">
          <CardHeader>
            <div class="flex items-center gap-3">
              <span class="flex size-9 items-center justify-center rounded-lg bg-muted"><Building class="size-4" /></span>
              <div>
                <CardTitle><RouterLink :to="`/buildings/${b.name}`" class="hover:underline">{{ b.building_name }}</RouterLink></CardTitle>
                <p class="tabular text-xs text-muted-foreground">{{ b.rooms }} rooms · {{ b.occupied }}/{{ b.beds }} beds occupied</p>
              </div>
            </div>
            <Button v-if="can('PG Floor', 'create')" variant="ghost" size="sm" @click="addFloor(b.name)"><Plus />Floor</Button>
          </CardHeader>
          <CardContent>
            <p v-if="!b.floors.length" class="text-sm text-muted-foreground">No floors yet.</p>
            <ul class="divide-y">
              <li v-for="f in b.floors" :key="f.name">
                <RouterLink :to="{ path: '/rooms', query: { building: b.name, floor: f.name } }" class="-mx-2 flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-muted/50">
                  <Layers class="size-4 text-muted-foreground" />
                  <span class="flex-1 text-sm font-medium">{{ f.floor_name }}</span>
                  <span class="tabular text-xs text-muted-foreground">{{ f.rooms }} rooms · {{ f.occupied }}/{{ f.beds }}</span>
                </RouterLink>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
      <BuildingFormDialog v-model:open="buildingOpen" :property="name" @saved="run" />
      <FloorFormDialog v-model:open="floorOpen" :property="name" :building="floorBuilding" @saved="run" />
    </template>
  </div>
</template>
