<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Sparkles } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import Money from '@/components/common/Money.vue'
import GenerateInvoicesDialog from '@/components/rent/GenerateInvoicesDialog.vue'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import { downloadCsv } from '@/utils/export'
import { formatMonth } from '@/utils/date'
import type { Invoice } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const { filters, activeCount, reset } = useFilters({ status: '', month: '' })
const list = useResourceList<Invoice>('PG Rent Invoice', {
  filters: () => ({
    status: filters.status,
    period_start: filters.month ? `${filters.month.slice(0, 7)}-01` : '',
  }),
  orderBy: 'due_date desc',
})
const genOpen = ref(false)
const columns = computed(() => [
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'name', label: 'Invoice', mobileHidden: true },
  { key: 'period_start', label: 'Period' },
  { key: 'due_date', label: 'Due', format: 'date' as const, sortable: true },
  { key: 'total_amount', label: 'Total', format: 'currency' as const, align: 'right' as const },
  { key: 'outstanding_amount', label: 'Outstanding', align: 'right' as const, sortable: true },
  { key: 'status', label: 'Status', format: 'status' as const },
])
function exportCsv() {
  downloadCsv('invoices.csv', list.rows.value, [
    ['Invoice', 'name'], ['Tenant', 'tenant_name'], ['Property', 'property'], ['Period', 'period_start'], ['Due', 'due_date'],
    ['Total', 'total_amount'], ['Paid', 'paid_amount'], ['Outstanding', 'outstanding_amount'], ['Status', 'status'],
  ])
}
</script>

<template>
  <div>
    <PageHeader title="Invoices" :description="`${list.total.value} invoices`">
      <template #actions>
        <Button variant="outline" :disabled="!list.rows.value.length" @click="exportCsv"><Download />Export</Button>
        <Button v-if="can('PG Rent Invoice', 'create')" @click="genOpen = true"><Sparkles />Generate</Button>
      </template>
    </PageHeader>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Tenant or invoice no…" /></template>
        <NativeSelect v-model="filters.status" :options="['Unpaid', 'Partially Paid', 'Overdue', 'Paid', 'Draft', 'Cancelled']" placeholder="All statuses" class="lg:w-44" />
        <Input v-model="filters.month" type="month" class="lg:w-44" aria-label="Billing month" />
      </FilterPanel>
    </div>
    <DataTable
      v-model:sort="list.orderBy.value"
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No invoices"
      empty-description="Generate this month's invoices from the Rent page."
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/rent/invoices/${r.name}`)"
      @retry="list.reload"
    >
      <template #cell-period_start="{ value }">{{ formatMonth(value) }}</template>
      <template #cell-outstanding_amount="{ value }"><Money :value="value" tone="danger" /></template>
    </DataTable>
    <GenerateInvoicesDialog v-model:open="genOpen" @done="list.reload" />
  </div>
</template>
