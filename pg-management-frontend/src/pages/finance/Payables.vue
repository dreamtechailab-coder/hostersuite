<script setup lang="ts">
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { CheckCircle2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import { reportService } from '@/services/report.service'
import { expenseService } from '@/services/payment.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { formatCurrency } from '@/utils/currency'
import { dueLabel } from '@/utils/date'

const router = useRouter()
const { can } = usePermissions()
const property = usePropertyStore()
const { data, loading, error, run } = useAsync(() => reportService.payables(property.filter))
watch(() => property.filter, () => run(), { immediate: true })
const pay = useMutation((n: string) => expenseService.markPaid(n))
async function markPaid(n: string) {
  if (await pay.run(n)) run()
}
</script>

<template>
  <div>
    <PageHeader title="Payables" description="Unpaid bills and security deposits owed back to tenants." />
    <div class="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatCard label="Unpaid expenses" :value="formatCurrency(data?.totals.unpaid_expenses)" tone="warning" :loading="loading" />
      <StatCard label="Overdue bills" :value="formatCurrency(data?.totals.overdue_expenses)" :tone="data?.totals.overdue_expenses ? 'danger' : 'success'" :loading="loading" />
      <StatCard label="Deposits to refund" :value="formatCurrency(data?.totals.deposits_to_refund)" hint="Checked-out tenants" tone="info" :loading="loading" />
      <StatCard label="Deposits held" :value="formatCurrency(data?.totals.deposits_held)" hint="Current tenants (liability)" :loading="loading" />
    </div>
    <h2 class="mb-3 font-semibold">Unpaid expenses</h2>
    <DataTable
      :columns="[
        { key: 'vendor', label: 'Vendor' },
        { key: 'category', label: 'Category' },
        { key: 'property', label: 'Property', mobileHidden: true },
        { key: 'due_date', label: 'Due' },
        { key: 'amount', label: 'Amount', format: 'currency', align: 'right' },
      ]"
      :rows="data?.expenses || []"
      :loading="loading"
      :error="error"
      clickable
      empty-title="No unpaid bills"
      @row-click="(r) => router.push(`/expenses/${r.name}/edit`)"
      @retry="run"
    >
      <template #cell-vendor="{ row }">{{ row.vendor || row.category }}</template>
      <template #cell-due_date="{ value }"><span :class="value && dueLabel(value).startsWith('Overdue') ? 'text-destructive' : ''">{{ dueLabel(value) || '—' }}</span></template>
      <template v-if="can('PG Expense', 'write')" #row-actions="{ row }"><Button size="sm" variant="outline" @click="markPaid(row.name)"><CheckCircle2 />Mark paid</Button></template>
    </DataTable>
    <h2 class="mb-3 mt-8 font-semibold">Deposits pending refund</h2>
    <DataTable
      :columns="[
        { key: 'tenant_name', label: 'Tenant' },
        { key: 'property', label: 'Property' },
        { key: 'check_out_date', label: 'Checked out', format: 'date' },
        { key: 'security_deposit', label: 'Deposit', format: 'currency', align: 'right' },
      ]"
      :rows="data?.deposits_due || []"
      :loading="loading"
      clickable
      empty-title="No deposits pending refund"
      @row-click="(r) => router.push(`/tenants/${r.tenant}`)"
    />
  </div>
</template>
