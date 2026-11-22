<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Plus, Users, Phone } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Avatar } from '@/components/ui/avatar'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import type { Tenant } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const { filters, activeCount, reset } = useFilters({ status: '' })
const list = useResourceList<Tenant>('PG Tenant', { filters: () => ({ status: filters.status }) })
const columns = [
  { key: 'full_name', label: 'Tenant', sortable: true },
  { key: 'mobile', label: 'Mobile' },
  { key: 'property', label: 'Property', mobileHidden: true },
  { key: 'occupation', label: 'Occupation', mobileHidden: true },
  { key: 'status', label: 'Status', format: 'status' as const },
]
</script>

<template>
  <div>
    <PageHeader title="Tenants" :description="`${list.total.value} tenants`">
      <template #actions>
        <Button v-if="can('PG Tenant', 'create')" as-child><RouterLink to="/tenants/new"><Plus />Add tenant</RouterLink></Button>
      </template>
    </PageHeader>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Name, mobile or email…" /></template>
        <NativeSelect v-model="filters.status" :options="['Prospective', 'Active', 'On Notice', 'Vacated']" placeholder="All statuses" class="lg:w-44" />
      </FilterPanel>
    </div>
    <DataTable
      v-model:sort="list.orderBy.value"
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No tenants found"
      empty-description="Add a tenant to create bookings and check them in."
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/tenants/${r.name}`)"
      @retry="list.reload"
    >
      <template #cell-full_name="{ row }">
        <span class="flex items-center gap-3">
          <Avatar :name="row.full_name" :src="row.photo" class="size-8" />
          <span class="min-w-0">
            <span class="block truncate font-medium">{{ row.full_name }}</span>
            <span class="block truncate text-xs text-muted-foreground md:hidden">{{ row.mobile }}</span>
          </span>
        </span>
      </template>
      <template #cell-mobile="{ row }">
        <a :href="`tel:${row.mobile}`" class="inline-flex items-center gap-1 hover:text-primary" @click.stop><Phone class="size-3.5" />{{ row.mobile }}</a>
      </template>
      <template #mobile-card="{ row }">
        <button type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left active:bg-muted/60" @click="router.push(`/tenants/${row.name}`)">
          <Avatar :name="row.full_name" :src="row.photo" />
          <span class="min-w-0 flex-1">
            <span class="block truncate font-medium">{{ row.full_name }}</span>
            <span class="block truncate text-xs text-muted-foreground">{{ row.mobile }} · {{ row.property }}</span>
          </span>
          <StatusBadge :status="row.status" />
        </button>
      </template>
      <template #empty>
        <Button v-if="can('PG Tenant', 'create')" as-child><RouterLink to="/tenants/new"><Users />Add tenant</RouterLink></Button>
      </template>
    </DataTable>
  </div>
</template>
