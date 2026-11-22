<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, CheckCircle2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatCard from '@/components/common/StatCard.vue'
import { expenseService } from '@/services/payment.service'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { downloadCsv } from '@/utils/export'
import { formatCurrency } from '@/utils/currency'
import { monthEnd, monthStart } from '@/utils/date'
import type { Expense } from '@/types'

const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const { filters, activeCount, reset } = useFilters({ category: '', payment_status: '', from: monthStart(), to: monthEnd() })
const list = useResourceList<Expense>('PG Expense', {
  filters: () => ({ category: filters.category, payment_status: filters.payment_status, expense_date: filters.from && filters.to ? ['between', [filters.from, filters.to]] : '' }),
})
const summary = useAsync(() => expenseService.summary(property.filter, filters.from, filters.to))
watch([() => property.filter, () => filters.from, () => filters.to], () => summary.run(), { immediate: true })
const markPaid = useMutation((n: string) => expenseService.markPaid(n))
async function pay(e: Expense) {
  if (await markPaid.run(e.name)) {
    list.reload()
    summary.run()
  }
}
const columns = [
  { key: 'expense_date', label: 'Date', format: 'date' as const, sortable: true },
  { key: 'category', label: 'Category' },
  { key: 'vendor', label: 'Vendor' },
  { key: 'property', label: 'Property', mobileHidden: true },
  { key: 'amount', label: 'Amount', format: 'currency' as const, align: 'right' as const, sortable: true },
  { key: 'payment_status', label: 'Status', format: 'status' as const },
]
const exportCsv = () => downloadCsv('expenses.csv', list.rows.value, [['Date', 'expense_date'], ['Category', 'category'], ['Vendor', 'vendor'], ['Property', 'property'], ['Amount', 'amount'], ['Status', 'payment_status'], ['Description', 'description']])
const top = ref(3)
</script>

<template>
  <div>
    <PageHeader title="Expenses">
      <template #actions>
        <Button variant="outline" :disabled="!list.rows.value.length" @click="exportCsv"><Download />Export</Button>
        <Button v-if="can('PG Expense', 'create')" as-child><RouterLink to="/expenses/new"><Plus />Add expense</RouterLink></Button>
      </template>
    </PageHeader>
    <div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatCard label="Total spent" :value="formatCurrency(summary.data.value?.totals.total)" :hint="`${summary.data.value?.totals.count ?? 0} expenses`" :loading="summary.loading.value" />
      <StatCard label="Unpaid" :value="formatCurrency(summary.data.value?.totals.unpaid)" :tone="summary.data.value?.totals.unpaid ? 'warning' : 'success'" :loading="summary.loading.value" to="/finance/payables" />
      <StatCard v-for="c in (summary.data.value?.by_category || []).slice(0, top - 1)" :key="c.name" :label="c.name" :value="formatCurrency(c.value)" :hint="`${c.count} entries`" class="hidden lg:flex" />
    </div>
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Vendor or description…" /></template>
        <SearchSelect v-model="filters.category" doctype="PG Expense Category" placeholder="All categories" class="lg:w-48" />
        <NativeSelect v-model="filters.payment_status" :options="['Paid', 'Unpaid']" placeholder="Paid & unpaid" class="lg:w-36" />
        <Input v-model="filters.from" type="date" class="lg:w-40" aria-label="From date" />
        <Input v-model="filters.to" type="date" class="lg:w-40" aria-label="To date" />
      </FilterPanel>
    </div>
    <DataTable
      v-model:sort="list.orderBy.value"
      :columns="columns"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No expenses in this period"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => can('PG Expense', 'write') && router.push(`/expenses/${r.name}/edit`)"
      @retry="list.reload"
    >
      <template v-if="can('PG Expense', 'write')" #row-actions="{ row }">
        <Button v-if="row.payment_status === 'Unpaid'" size="sm" variant="outline" @click="pay(row)"><CheckCircle2 />Mark paid</Button>
      </template>
    </DataTable>
  </div>
</template>
