<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Pencil, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import DataTable from '@/components/common/DataTable.vue'
import FloorFormDialog from '@/components/floor/FloorFormDialog.vue'
import { useResourceList } from '@/composables/useResourceList'
import { usePermissions } from '@/composables/usePermissions'
import { useFilters } from '@/composables/useFilters'
import { useConfirm } from '@/composables/useConfirm'
import { useMutation } from '@/composables/useMutation'
import { resource } from '@/services/resource.service'
import { usePropertyStore } from '@/stores/property'
import type { Floor } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const { filters, activeCount, reset } = useFilters({ building: '' })
const list = useResourceList<Floor>('PG Floor', { filters: () => ({ building: filters.building }), orderBy: 'floor_number asc' })
const open = ref(false)
const editing = ref<Floor | null>(null)
const { confirm } = useConfirm()
const del = useMutation((n: string) => resource.remove('PG Floor', n), { success: 'Floor deleted' })
async function remove(f: Floor) {
  const { confirmed } = await confirm({ title: `Delete ${f.floor_name}?`, description: 'Floors with rooms cannot be deleted.', destructive: true, confirmText: 'Delete' })
  if (confirmed && (await del.run(f.name))) list.reload()
}
const columns = computed(() => [
  { key: 'floor_name', label: 'Floor' },
  { key: 'floor_number', label: 'Level', align: 'right' as const },
  { key: 'building', label: 'Building' },
  { key: 'property', label: 'Property' },
])
</script>

<template>
  <div>
    <PageHeader title="Floors">
      <template #actions>
        <Button v-if="can('PG Floor', 'create')" @click="(editing = null), (open = true)"><Plus />Add floor</Button>
      </template>
    </PageHeader>
    <div class="mb-3">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Search floors…" /></template>
        <SearchSelect v-model="filters.building" doctype="PG Building" :filters="property.filter ? { property: property.filter } : undefined" placeholder="All buildings" class="lg:w-56" />
      </FilterPanel>
    </div>
    <DataTable
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push({ path: '/rooms', query: { building: r.building, floor: r.name } })"
      @retry="list.reload"
    >
      <template v-if="can('PG Floor', 'write')" #row-actions="{ row }">
        <Button variant="ghost" size="icon-sm" :aria-label="`Edit ${row.floor_name}`" @click="(editing = row), (open = true)"><Pencil /></Button>
        <Button v-if="can('PG Floor', 'delete')" variant="ghost" size="icon-sm" :aria-label="`Delete ${row.floor_name}`" @click="remove(row)"><Trash2 /></Button>
      </template>
    </DataTable>
    <FloorFormDialog v-model:open="open" :floor="editing" :property="property.filter" :building="filters.building" @saved="list.reload" />
  </div>
</template>
