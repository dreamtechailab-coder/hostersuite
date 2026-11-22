<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Check, X, LogIn } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import CheckInDialog from '@/components/occupancy/CheckInDialog.vue'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { bookingService } from '@/services/tenant.service'
import type { Booking } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const { confirm } = useConfirm()
const { filters, activeCount, reset } = useFilters({ status: 'open' })
const list = useResourceList<Booking>('PG Booking', {
  filters: () => ({ status: filters.status === 'open' ? ['in', ['Pending', 'Confirmed']] : filters.status }),
})
const confirmM = useMutation(bookingService.confirm)
const cancelM = useMutation(bookingService.cancel)
async function onConfirm(b: Booking) {
  if (await confirmM.run(b.name)) list.reload()
}
async function onCancel(b: Booking) {
  const res = await confirm({ title: `Cancel booking for ${b.tenant_name}?`, description: 'Any reserved bed will be released.', destructive: true, confirmText: 'Cancel booking', cancelText: 'Keep', withReason: true })
  if (res.confirmed && (await cancelM.run(b.name, res.reason))) list.reload()
}
const ci = ref<Booking | null>(null)
const ciOpen = ref(false)
function checkIn(b: Booking) {
  if (!b.bed || b.status !== 'Confirmed') return router.push({ path: '/rooms/allocate', query: { tenant: b.tenant, booking: b.name } })
  ci.value = b
  ciOpen.value = true
}
const columns = [
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'room', label: 'Room', mobileHidden: true },
  { key: 'expected_check_in', label: 'Check-in', format: 'date' as const },
  { key: 'advance_amount', label: 'Advance', format: 'currency' as const, align: 'right' as const },
  { key: 'status', label: 'Status', format: 'status' as const },
]
</script>

<template>
  <div>
    <PageHeader title="Bookings" description="Reservations awaiting check-in.">
      <template #actions>
        <Button v-if="can('PG Booking', 'create')" as-child><RouterLink to="/bookings/new"><Plus />New booking</RouterLink></Button>
      </template>
    </PageHeader>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Search tenant or booking…" /></template>
        <NativeSelect v-model="filters.status" :options="[{ value: 'open', label: 'Open (pending + confirmed)' }, 'Pending', 'Confirmed', 'Checked In', 'Cancelled']" placeholder="All" class="lg:w-56" />
      </FilterPanel>
    </div>
    <DataTable
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No bookings"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/tenants/${r.tenant}`)"
      @retry="list.reload"
    >
      <template #row-actions="{ row }">
        <div class="flex justify-end gap-1">
          <Button v-if="row.status === 'Pending' && can('PG Booking', 'write')" size="sm" variant="outline" @click="onConfirm(row)"><Check />Confirm</Button>
          <Button v-if="['Pending', 'Confirmed'].includes(row.status) && can('PG Occupancy', 'create')" size="sm" @click="checkIn(row)"><LogIn />Check in</Button>
          <Button v-if="['Pending', 'Confirmed'].includes(row.status) && can('PG Booking', 'write')" size="icon-sm" variant="ghost" :aria-label="`Cancel booking ${row.name}`" @click="onCancel(row)"><X /></Button>
        </div>
      </template>
    </DataTable>
    <CheckInDialog v-if="ci" v-model:open="ciOpen" :tenant="ci.tenant" :tenant-label="ci.tenant_name" :bed="ci.bed" :booking="ci.name" :property="ci.property" @done="list.reload" />
  </div>
</template>
