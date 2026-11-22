<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Download, Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import PaymentCard from '@/components/payments/PaymentCard.vue'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { usePermissions } from '@/composables/usePermissions'
import { downloadCsv } from '@/utils/export'
import { formatCurrency } from '@/utils/currency'
import type { Payment } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const { filters, activeCount, reset } = useFilters({ mode: '', from: '', to: '', show: 'valid' })
const list = useResourceList<Payment>('PG Payment', {
  filters: () => ({
    mode: filters.mode,
    docstatus: filters.show === 'cancelled' ? 2 : 1,
    payment_date: filters.from && filters.to ? ['between', [filters.from, filters.to]] : filters.from ? ['>=', filters.from] : filters.to ? ['<=', filters.to] : '',
  }),
})
const columns = [
  { key: 'payment_date', label: 'Date', format: 'date' as const, sortable: true },
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'mode', label: 'Mode' },
  { key: 'reference_no', label: 'Reference', mobileHidden: true },
  { key: 'name', label: 'Receipt', mobileHidden: true },
  { key: 'amount', label: 'Amount', align: 'right' as const, sortable: true },
]
function exportCsv() {
  downloadCsv('payments.csv', list.rows.value, [['Receipt', 'name'], ['Date', 'payment_date'], ['Tenant', 'tenant_name'], ['Property', 'property'], ['Mode', 'mode'], ['Reference', 'reference_no'], ['Amount', 'amount']])
}
</script>

<template>
  <div>
    <PageHeader title="Payments" :description="`${list.total.value} payments`">
      <template #actions>
        <Button variant="outline" :disabled="!list.rows.value.length" @click="exportCsv"><Download />Export</Button>
        <Button v-if="can('PG Payment', 'create')" as-child><RouterLink to="/payments/collect"><Plus />Collect payment</RouterLink></Button>
      </template>
    </PageHeader>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Tenant, reference…" /></template>
        <NativeSelect v-model="filters.mode" :options="['Cash', 'UPI', 'Bank Transfer', 'Card', 'Cheque']" placeholder="Any mode" class="lg:w-40" />
        <Input v-model="filters.from" type="date" class="lg:w-40" aria-label="From date" />
        <Input v-model="filters.to" type="date" class="lg:w-40" aria-label="To date" />
        <NativeSelect v-model="filters.show" :options="[{ value: 'valid', label: 'Recorded' }, { value: 'cancelled', label: 'Cancelled' }]" class="lg:w-36" />
      </FilterPanel>
    </div>
    <DataTable
      v-model:sort="list.orderBy.value"
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No payments found"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => router.push(`/payments/${r.name}`)"
      @retry="list.reload"
    >
      <template #cell-amount="{ row }"><span :class="['tabular font-medium', row.docstatus === 2 ? 'text-muted-foreground line-through' : 'text-success']">{{ formatCurrency(row.amount) }}</span></template>
      <template #mobile-card="{ row }"><PaymentCard :payment="row" /></template>
    </DataTable>
  </div>
</template>
