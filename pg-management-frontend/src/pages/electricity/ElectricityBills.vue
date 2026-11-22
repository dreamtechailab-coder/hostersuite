<script setup lang="ts">
import { ref, watch } from 'vue'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import Pagination from '@/components/common/Pagination.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { Card } from '@/components/ui/card'
import { electricityService } from '@/services/rent.service'
import { useAsync } from '@/composables/useAsync'
import { useFilters } from '@/composables/useFilters'
import { usePagination } from '@/composables/usePagination'
import { usePropertyStore } from '@/stores/property'
import { formatCurrency, formatNumber } from '@/utils/currency'
import { formatDate } from '@/utils/date'
import { Zap } from 'lucide-vue-next'

const property = usePropertyStore()
const { filters, activeCount, reset } = useFilters({ billing_status: '' })
const pg = usePagination(10)
const { data, loading, error, run } = useAsync(async () => {
  const res = await electricityService.bills({ property: property.filter, billing_status: filters.billing_status || undefined, page: pg.page.value, page_size: pg.pageSize.value })
  pg.total.value = res.total
  return res.data
})
watch([() => property.filter, () => filters.billing_status], () => (pg.page.value === 1 ? run() : (pg.page.value = 1)), { immediate: true })
watch(pg.page, () => run())
const expanded = ref<string | null>(null)
</script>

<template>
  <div>
    <PageHeader title="Electricity bills" description="Each reading is split among the room's occupants and added to their next invoice." back="/electricity" />
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <NativeSelect v-model="filters.billing_status" :options="['Unbilled', 'Partially Billed', 'Billed']" placeholder="Any billing status" class="lg:w-52" />
      </FilterPanel>
    </div>
    <ErrorState v-if="error" :error="error" @retry="run" />
    <LoadingSkeleton v-else-if="loading && !data" variant="cards" :rows="4" />
    <EmptyState v-else-if="!data?.length" :icon="Zap" title="No electricity bills" description="Record meter readings to generate bills." />
    <div v-else class="space-y-3">
      <Card v-for="b in data" :key="b.name" class="overflow-hidden">
        <button type="button" class="flex w-full items-center gap-4 p-4 text-left hover:bg-muted/40" :aria-expanded="expanded === b.name" @click="expanded = expanded === b.name ? null : b.name">
          <span class="flex size-10 items-center justify-center rounded-lg bg-warning-soft text-warning"><Zap class="size-5" /></span>
          <span class="min-w-0 flex-1">
            <span class="block font-medium">Room {{ b.room_number }}</span>
            <span class="block text-xs text-muted-foreground">{{ formatDate(b.period_start, { day: 'numeric', month: 'short' }) }} – {{ formatDate(b.period_end) }} · <span class="tabular">{{ formatNumber(b.units_consumed, 1) }} units</span></span>
          </span>
          <span class="text-right">
            <span class="tabular block font-semibold">{{ formatCurrency(b.amount) }}</span>
            <StatusBadge :status="b.billing_status" />
          </span>
        </button>
        <div v-if="expanded === b.name" class="border-t bg-muted/20 px-4 py-3">
          <p v-if="!b.shares?.length" class="text-sm text-muted-foreground">Room was vacant during this period.</p>
          <table v-else class="w-full text-sm">
            <thead class="text-xs text-muted-foreground"><tr><th class="py-1 text-left font-medium">Tenant</th><th class="py-1 text-right font-medium">Days</th><th class="py-1 text-right font-medium">Share</th><th class="py-1 text-right font-medium">Invoice</th></tr></thead>
            <tbody>
              <tr v-for="s in b.shares" :key="s.tenant">
                <td class="py-1.5">{{ s.tenant_name }}</td>
                <td class="tabular py-1.5 text-right">{{ s.days }}</td>
                <td class="tabular py-1.5 text-right">{{ formatCurrency(s.amount) }}</td>
                <td class="py-1.5 text-right"><RouterLink v-if="s.invoice" :to="`/rent/invoices/${s.invoice}`" class="text-primary hover:underline">{{ s.invoice }}</RouterLink><span v-else class="text-muted-foreground">Pending</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
      <div class="rounded-xl border bg-card"><Pagination :page="pg.page.value" :page-count="pg.pageCount.value" :total="pg.total.value" :from="pg.from.value" :to="pg.to.value" @update:page="pg.setPage" /></div>
    </div>
  </div>
</template>
