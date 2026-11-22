<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarClock, LogOut } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import CheckOutDialog from '@/components/occupancy/CheckOutDialog.vue'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import { useTenantStore } from '@/stores/tenant'
import type { Occupancy } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const tenantStore = useTenantStore()
const { filters, activeCount, reset } = useFilters({ status: 'current' })
const list = useResourceList<Occupancy>('PG Occupancy', {
  filters: () => ({ status: filters.status === 'current' ? ['!=', 'Ended'] : filters.status }),
})
const sel = ref<Occupancy | null>(null)
const open = ref(false)
const mode = ref<'notice' | 'checkout'>('checkout')
function act(o: Occupancy, m: 'notice' | 'checkout') {
  sel.value = o
  mode.value = m
  open.value = true
}
function done() {
  tenantStore.invalidate()
  list.reload()
}
const columns = [
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'room', label: 'Room', mobileHidden: true },
  { key: 'check_in_date', label: 'Check-in', format: 'date' as const },
  { key: 'expected_check_out', label: 'Leaving', format: 'date' as const },
  { key: 'monthly_rent', label: 'Rent', format: 'currency' as const, align: 'right' as const },
  { key: 'status', label: 'Status', format: 'status' as const },
]
</script>

<template>
  <div>
    <PageHeader title="Occupancy" description="Who is staying where, and who is leaving." />
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Search tenant…" /></template>
        <NativeSelect v-model="filters.status" :options="[{ value: 'current', label: 'Current (active + notice)' }, 'Active', 'On Notice', 'Ended']" placeholder="All" class="lg:w-56" />
      </FilterPanel>
    </div>
    <DataTable
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No occupancies"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/tenants/${r.tenant}`)"
      @retry="list.reload"
    >
      <template v-if="can('PG Occupancy', 'write')" #row-actions="{ row }">
        <div v-if="row.status !== 'Ended'" class="flex justify-end gap-1">
          <Button v-if="row.status === 'Active'" size="sm" variant="ghost" @click="act(row, 'notice')"><CalendarClock />Notice</Button>
          <Button size="sm" variant="outline" @click="act(row, 'checkout')"><LogOut />Check out</Button>
        </div>
      </template>
    </DataTable>
    <CheckOutDialog v-model:open="open" :occupancy="sel" :mode="mode" @done="done" />
  </div>
</template>
