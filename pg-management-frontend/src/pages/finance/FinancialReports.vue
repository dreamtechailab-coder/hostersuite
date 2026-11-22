<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Download } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import RevenueChart from '@/components/dashboard/RevenueChart.vue'
import ExpenseChart from '@/components/dashboard/ExpenseChart.vue'
import { reportService } from '@/services/report.service'
import { useAsync } from '@/composables/useAsync'
import { usePropertyStore } from '@/stores/property'
import { downloadCsv } from '@/utils/export'
import { formatCurrency } from '@/utils/currency'

const property = usePropertyStore()
const thisYear = new Date().getFullYear()
const year = ref(thisYear)
const { data, loading, error, run } = useAsync(() => reportService.financialSummary(property.filter, year.value))
watch([() => property.filter, year], () => run(), { immediate: true })
const months = computed(() => (data.value?.months || []).map((m) => `${year.value}-${String(m.month).padStart(2, '0')}`))
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
function exportCsv() {
  downloadCsv(`financial-summary-${year.value}.csv`, (data.value?.months || []).map((m) => ({ ...m, month: MONTHS[m.month - 1] })), [['Month', 'month'], ['Invoiced', 'invoiced'], ['Collected', 'collected'], ['Expenses', 'expenses'], ['Net', 'net']])
}
</script>

<template>
  <div>
    <PageHeader title="Financial reports" :description="`Income vs expenses · ${property.label}`">
      <template #actions>
        <NativeSelect v-model.number="year" :options="[0, 1, 2, 3].map((i) => ({ value: thisYear - i, label: String(thisYear - i) }))" class="w-28" aria-label="Year" />
        <Button variant="outline" :disabled="!data" @click="exportCsv"><Download />Export</Button>
      </template>
    </PageHeader>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <template v-else>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Invoiced" :value="formatCurrency(data?.totals.invoiced)" :loading="loading" />
        <StatCard label="Collected" :value="formatCurrency(data?.totals.collected)" tone="success" :loading="loading" />
        <StatCard label="Expenses" :value="formatCurrency(data?.totals.expenses)" tone="warning" :loading="loading" />
        <StatCard label="Net profit" :value="formatCurrency(data?.totals.net)" :tone="(data?.totals.net || 0) >= 0 ? 'success' : 'danger'" :loading="loading" />
      </div>
      <Card class="mt-5">
        <CardHeader><div><CardTitle>Monthly performance</CardTitle><CardDescription>{{ year }}</CardDescription></div></CardHeader>
        <CardContent v-if="data">
          <RevenueChart :months="months" :invoiced="data.months.map((m) => m.invoiced)" :collected="data.months.map((m) => m.collected)" :expenses="data.months.map((m) => m.expenses)" :height="300" />
        </CardContent>
      </Card>
      <div class="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Income by type</CardTitle></CardHeader>
          <CardContent>
            <ul class="divide-y">
              <li v-for="r in data?.income_by_type || []" :key="r.name" class="flex justify-between py-2.5 text-sm"><span>{{ r.name }}</span><span class="tabular font-medium">{{ formatCurrency(r.value) }}</span></li>
              <li v-if="!data?.income_by_type.length" class="py-6 text-center text-sm text-muted-foreground">No income recorded</li>
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Expenses by category</CardTitle></CardHeader>
          <CardContent><ExpenseChart :data="data?.expense_by_category || []" /></CardContent>
        </Card>
      </div>
      <Card class="mt-5 overflow-hidden">
        <CardHeader><CardTitle>Profit & loss</CardTitle></CardHeader>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
              <tr><th class="px-5 py-2 text-left font-medium">Month</th><th class="px-5 py-2 text-right font-medium">Invoiced</th><th class="px-5 py-2 text-right font-medium">Collected</th><th class="px-5 py-2 text-right font-medium">Expenses</th><th class="px-5 py-2 text-right font-medium">Net</th></tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="m in data?.months || []" :key="m.month">
                <td class="px-5 py-2.5">{{ MONTHS[m.month - 1] }}</td>
                <td class="tabular px-5 py-2.5 text-right">{{ formatCurrency(m.invoiced) }}</td>
                <td class="tabular px-5 py-2.5 text-right">{{ formatCurrency(m.collected) }}</td>
                <td class="tabular px-5 py-2.5 text-right">{{ formatCurrency(m.expenses) }}</td>
                <td :class="['tabular px-5 py-2.5 text-right font-medium', m.net < 0 ? 'text-destructive' : '']">{{ formatCurrency(m.net) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </template>
  </div>
</template>
