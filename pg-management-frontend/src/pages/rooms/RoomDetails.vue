<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Pencil, Trash2, Wrench, LogIn, Gauge, Snowflake, Bath } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import DetailList from '@/components/common/DetailList.vue'
import DataTable from '@/components/common/DataTable.vue'
import BedCard from '@/components/room/BedCard.vue'
import RoomFormDialog from '@/components/room/RoomFormDialog.vue'
import CheckInDialog from '@/components/occupancy/CheckInDialog.vue'
import { roomService } from '@/services/property.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { formatCurrency, formatNumber } from '@/utils/currency'
import { formatDate } from '@/utils/date'
import type { Bed } from '@/types'

const props = defineProps<{ name: string }>()
const router = useRouter()
const { can } = usePermissions()
const { confirm } = useConfirm()
const { data, loading, error, run } = useAsync(() => roomService.details(props.name), { immediate: true })
const editOpen = ref(false)
const checkInOpen = ref(false)
const bed = ref('')
const bedStatus = useMutation((b: string, s: 'Vacant' | 'Maintenance') => roomService.setBedStatus(b, s))
const del = useMutation(() => roomService.remove(props.name), { success: 'Room deleted' })

function onBed(b: Bed) {
  if (b.status === 'Occupied' && b.current_tenant) router.push(`/tenants/${b.current_tenant}`)
}
function startCheckIn(b: Bed) {
  bed.value = b.name
  checkInOpen.value = true
}
async function toggleMaintenance(b: Bed) {
  if (await bedStatus.run(b.name, b.status === 'Maintenance' ? 'Vacant' : 'Maintenance')) run()
}
async function remove() {
  const { confirmed } = await confirm({ title: 'Delete this room?', description: 'Its beds will also be removed. Rooms with occupied or reserved beds cannot be deleted.', destructive: true, confirmText: 'Delete room' })
  if (confirmed && (await del.run())) router.replace('/rooms')
}
</script>

<template>
  <div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data">
      <PageHeader :title="`Room ${data.room.room_number}`" :description="`${data.room.property} · ${data.building_name} · ${data.floor_name}`" back="/rooms">
        <template #badge><StatusBadge :status="data.room.status" /></template>
        <template #actions>
          <Button v-if="can('PG Room', 'write')" variant="outline" @click="editOpen = true"><Pencil />Edit</Button>
          <Button v-if="can('PG Room', 'delete')" variant="outline" aria-label="Delete room" @click="remove"><Trash2 /></Button>
        </template>
      </PageHeader>

      <div class="grid gap-5 lg:grid-cols-3">
        <Card class="lg:col-span-2">
          <CardHeader><CardTitle>Beds</CardTitle></CardHeader>
          <CardContent class="grid gap-3 sm:grid-cols-2">
            <div v-for="b in data.beds" :key="b.name" class="flex flex-col gap-2">
              <BedCard :bed="b" :interactive="b.status === 'Occupied'" @select="onBed" />
              <div class="flex gap-2">
                <Button v-if="b.status === 'Vacant' && can('PG Occupancy', 'create')" size="sm" variant="outline" class="flex-1" @click="startCheckIn(b)"><LogIn />Check in</Button>
                <Button v-if="(b.status === 'Vacant' || b.status === 'Maintenance') && can('PG Bed', 'write')" size="sm" variant="ghost" @click="toggleMaintenance(b)">
                  <Wrench />{{ b.status === 'Maintenance' ? 'Mark available' : 'Maintenance' }}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Details</CardTitle></CardHeader>
          <CardContent>
            <DetailList
              :items="[
                { label: 'Sharing', value: data.room.room_type },
                { label: 'Beds', value: `${data.room.occupied_beds || 0}/${data.room.capacity} occupied` },
                { label: 'Rent / bed', value: formatCurrency(data.room.rent_per_bed) },
                { label: 'Deposit / bed', value: formatCurrency(data.room.security_deposit) },
              ]"
            />
            <div class="mt-4 flex flex-wrap gap-3 text-sm text-muted-foreground">
              <span v-if="data.room.is_ac" class="inline-flex items-center gap-1"><Snowflake class="size-4" />AC</span>
              <span v-if="data.room.attached_bathroom" class="inline-flex items-center gap-1"><Bath class="size-4" />Attached bath</span>
            </div>
            <p v-if="data.room.amenities" class="mt-3 text-sm text-muted-foreground">{{ data.room.amenities }}</p>
          </CardContent>
        </Card>
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-3">
        <div class="lg:col-span-2">
          <h2 class="mb-3 font-semibold">Occupancy history</h2>
          <DataTable
            :columns="[
              { key: 'tenant_name', label: 'Tenant' },
              { key: 'check_in_date', label: 'Check-in', format: 'date' },
              { key: 'check_out_date', label: 'Check-out', format: 'date' },
              { key: 'monthly_rent', label: 'Rent', format: 'currency', align: 'right' },
              { key: 'status', label: 'Status', format: 'status' },
            ]"
            :rows="data.occupancies"
            clickable
            empty-title="No one has stayed here yet"
            @row-click="(r) => router.push(`/tenants/${r.tenant}`)"
          />
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Electricity</CardTitle>
            <DropdownMenu v-if="data.meters.length && can('PG Meter Reading', 'create')">
              <DropdownMenuTrigger as-child><Button size="sm" variant="outline"><Gauge />Reading</Button></DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem v-for="m in data.meters" :key="m.name" @select="router.push({ path: '/electricity/readings', query: { meter: m.name } })">Meter {{ m.meter_number }}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardHeader>
          <CardContent>
            <p v-if="!data.meters.length" class="text-sm text-muted-foreground">No meter linked. <RouterLink v-if="can('PG Electricity Meter', 'create')" to="/electricity/readings?addMeter=1" class="font-medium text-primary hover:underline">Add meter</RouterLink></p>
            <div v-for="m in data.meters" :key="m.name" class="mb-3 rounded-lg border p-3 text-sm">
              <p class="font-medium">Meter {{ m.meter_number }}</p>
              <p class="tabular text-muted-foreground">Last reading {{ formatNumber(m.last_reading, 2) }} on {{ formatDate(m.last_reading_date) }} · {{ formatCurrency(m.rate_per_unit) }}/unit</p>
            </div>
            <ul class="divide-y text-sm">
              <li v-for="r in data.readings" :key="r.name" class="flex justify-between py-2">
                <span>{{ formatDate(r.reading_date) }} · <span class="tabular">{{ formatNumber(r.units_consumed, 1) }} units</span></span>
                <span class="tabular font-medium">{{ formatCurrency(r.amount) }}</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <RoomFormDialog v-model:open="editOpen" :room="data.room" @saved="run" />
      <CheckInDialog v-model:open="checkInOpen" :bed="bed" :room="data.room" :property="data.room.property" @done="run" />
    </template>
  </div>
</template>
