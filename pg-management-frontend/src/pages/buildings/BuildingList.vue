<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Pencil } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import DataTable from '@/components/common/DataTable.vue'
import BuildingFormDialog from '@/components/building/BuildingFormDialog.vue'
import { useResourceList } from '@/composables/useResourceList'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import type { Building } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const list = useResourceList<Building>('PG Building')
const open = ref(false)
const editing = ref<Building | null>(null)
function edit(b: Building | null) {
  editing.value = b
  open.value = true
}
const columns = [
  { key: 'building_name', label: 'Building' },
  { key: 'property', label: 'Property' },
  { key: 'address_line', label: 'Address', mobileHidden: true },
  { key: 'is_active', label: 'Status' },
]
</script>

<template>
  <div>
    <PageHeader title="Buildings" description="Blocks and towers within your properties.">
      <template #actions>
        <SearchInput v-model="list.search.value" placeholder="Search buildings…" />
        <Button v-if="can('PG Building', 'create')" @click="edit(null)"><Plus />Add building</Button>
      </template>
    </PageHeader>
    <DataTable
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No buildings yet"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/buildings/${r.name}`)"
      @retry="list.reload"
    >
      <template #cell-is_active="{ value }"><span :class="value ? 'text-success' : 'text-muted-foreground'">{{ value ? 'Active' : 'Inactive' }}</span></template>
      <template v-if="can('PG Building', 'write')" #row-actions="{ row }">
        <Button variant="ghost" size="icon-sm" :aria-label="`Edit ${row.building_name}`" @click="edit(row)"><Pencil /></Button>
      </template>
    </DataTable>
    <BuildingFormDialog v-model:open="open" :building="editing" :property="property.filter" @saved="list.reload" />
  </div>
</template>
