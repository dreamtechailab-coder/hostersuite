<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { watchDebounced } from '@vueuse/core'
import { CreditCard, Download } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import Money from '@/components/common/Money.vue'
import { reportService } from '@/services/report.service'
import { useAsync } from '@/composables/useAsync'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { downloadCsv } from '@/utils/export'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const search = ref('')
const { data, loading, error, run } = useAsync(() => reportService.receivables(property.filter, search.value || undefined))
watch(() => property.filter, () => run(), { immediate: true })
watchDebounced(search, () => run(), { debounce: 300 })
const columns = [
  { key: 'tenant_name', label: 'Tenant' },
  { key: 'property', label: 'Property', mobileHidden: true },
  { key: 'current_due', label: 'Not yet due', align: 'right' as const, format: 'currency' as const },
  { key: 'd1_30', label: '1–30 days', align: 'right' as const },
  { key: 'd31_60', label: '31–60', align: 'right' as const },
  { key: 'd61_90', label: '61–90', align: 'right' as const },
  { key: 'd90_plus', label: '90+', align: 'right' as const },
  { key: 'outstanding', label: 'Total', align: 'right' as const },
]
function exportCsv() {
  downloadCsv('receivables.csv', data.value?.rows || [], [['Tenant', 'tenant_name'], ['Mobile', 'mobile'], ['Property', 'property'], ['Not due', 'current_due'], ['1-30', 'd1_30'], ['31-60', 'd31_60'], ['61-90', 'd61_90'], ['90+', 'd90_plus'], ['Total', 'outstanding']])
}
</script>

<template>
  <div>
    <PageHeader title="Receivables" description="Who owes what, aged by how late it is.">
      <template #actions>
        <SearchInput v-model="search" placeholder="Search tenant…" />
        <Button variant="outline" :disabled="!data?.rows.length" @click="exportCsv"><Download />Export</Button>
      </template>
    </PageHeader>
    <div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-5">
      <StatCard label="Total receivable" :value="formatCurrency(data?.totals.outstanding)" :loading="loading" />
      <StatCard label="Not yet due" :value="formatCurrency(data?.totals.current_due)" tone="info" :loading="loading" />
      <StatCard label="1–30 days late" :value="formatCurrency(data?.totals.d1_30)" tone="warning" :loading="loading" />
      <StatCard label="31–90 days late" :value="formatCurrency((data?.totals.d31_60 || 0) + (data?.totals.d61_90 || 0))" tone="danger" :loading="loading" />
      <StatCard label="90+ days late" :value="formatCurrency(data?.totals.d90_plus)" tone="danger" :loading="loading" />
    </div>
    <DataTable :columns="columns" :rows="data?.rows || []" :loading="loading" :error="error" row-key="tenant" clickable empty-title="No outstanding dues" empty-description="Every tenant is fully paid up." @row-click="(r) => router.push(`/tenants/${r.tenant}`)" @retry="run">
      <template #cell-tenant_name="{ row }"><span class="font-medium">{{ row.tenant_name }}</span><span class="block text-xs text-muted-foreground">{{ row.mobile }} · {{ row.invoices }} invoice(s)</span></template>
      <template v-for="k in ['d1_30', 'd31_60', 'd61_90', 'd90_plus']" :key="k" #[`cell-${k}`]="{ value }"><Money :value="value" tone="danger" /></template>
      <template #cell-outstanding="{ value }"><span class="tabular font-semibold">{{ formatCurrency(value) }}</span></template>
      <template v-if="can('PG Payment', 'create')" #row-actions="{ row }">
        <Button size="sm" variant="outline" @click="router.push({ path: '/payments/collect', query: { tenant: row.tenant } })"><CreditCard />Collect</Button>
      </template>
    </DataTable>
  </div>
</template>
