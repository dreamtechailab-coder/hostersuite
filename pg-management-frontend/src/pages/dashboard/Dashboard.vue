<script setup lang="ts">
import { computed, watch } from 'vue'
import { BedDouble, CalendarClock, CreditCard, Download, HandCoins, Plus, TrendingDown, Users, Wallet, X } from 'lucide-vue-next'
import { useLocalStorage } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import RevenueChart from '@/components/dashboard/RevenueChart.vue'
import ExpenseChart from '@/components/dashboard/ExpenseChart.vue'
import VacancyBar from '@/components/dashboard/VacancyBar.vue'
import PropertyComparison from '@/components/dashboard/PropertyComparison.vue'
import RecentTransactions from '@/components/dashboard/RecentTransactions.vue'
import UpcomingDues from '@/components/dashboard/UpcomingDues.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { usePropertyStore } from '@/stores/property'
import { useAuthStore } from '@/stores/auth'
import { usePwaInstall } from '@/composables/usePwa'
import { formatCurrency, formatPercent } from '@/utils/currency'
import { formatDate } from '@/utils/date'

const store = useDashboardStore()
const property = usePropertyStore()
const auth = useAuthStore()
const { canInstall, hasPrompt, install } = usePwaInstall()
const hideInstall = useLocalStorage('pg.hideInstallCard', false)

watch([() => property.filter, () => store.range], () => store.load(property.filter), { immediate: true, deep: true })

const d = computed(() => store.data)
const f = computed(() => d.value?.finance)
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
})
const rangeLabel = computed(() => (d.value ? `${formatDate(d.value.range.from, { day: 'numeric', month: 'short' })} – ${formatDate(d.value.range.to)}` : ''))
</script>

<template>
  <div>
    <PageHeader :title="`${greeting}, ${auth.user?.full_name?.split(' ')[0] || ''}`" :description="`${property.label} · ${rangeLabel}`">
      <template #actions>
        <DateRangePicker v-model="store.range" v-model:preset="store.preset" />
        <Button v-if="auth.can('PG Payment', 'create')" as-child class="hidden sm:inline-flex">
          <RouterLink to="/payments/collect"><Plus />Collect payment</RouterLink>
        </Button>
      </template>
    </PageHeader>

    <div v-if="canInstall && !hideInstall" class="mb-5 flex items-center gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
      <Download class="size-5 shrink-0 text-primary" />
      <p class="flex-1 text-sm"><span class="font-medium">Install HostelSuite</span> for one-tap access and a full-screen experience.</p>
      <Button v-if="hasPrompt" size="sm" @click="install">Install</Button>
      <Button variant="ghost" size="icon-sm" aria-label="Dismiss" @click="hideInstall = true"><X /></Button>
    </div>

    <ErrorState v-if="store.error && !d" :error="store.error" @retry="store.load(property.filter, true)" />
    <LoadingSkeleton v-else-if="!d" variant="stats" />
    <template v-else>
      <EmptyState
        v-if="!d.occupancy.total_beds && !auth.properties.length"
        title="Let's set up your first property"
        description="Add a property, its buildings, floors and rooms to start tracking occupancy and rent."
      >
        <Button v-if="auth.isAdmin" as-child><RouterLink to="/properties/new"><Plus />Add property</RouterLink></Button>
      </EmptyState>

      <section class="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="Key metrics">
        <StatCard
          label="Occupancy"
          :value="formatPercent(d.occupancy.rate)"
          :hint="`${d.occupancy.occupied} of ${d.occupancy.total_beds} beds occupied`"
          :icon="BedDouble"
          :progress="d.occupancy.rate"
          :loading="store.loading"
          to="/rooms"
        />
        <StatCard
          label="Active tenants"
          :value="d.occupancy.active_tenants"
          :hint="`${d.occupancy.on_notice} on notice · ${d.occupancy.check_ins} new`"
          :icon="Users"
          tone="info"
          :loading="store.loading"
          to="/tenants"
        />
        <template v-if="f">
          <StatCard
            label="Collected"
            :value="formatCurrency(f.collected, { compact: f.collected >= 1e6 })"
            :hint="`${formatPercent(f.collection_rate)} of ${formatCurrency(f.invoiced, { compact: true })} invoiced`"
            :icon="HandCoins"
            tone="success"
            :progress="f.collection_rate"
            :loading="store.loading"
            to="/payments"
          />
          <StatCard
            label="Overdue"
            :value="formatCurrency(f.overdue, { compact: f.overdue >= 1e6 })"
            :hint="`${formatCurrency(f.outstanding, { compact: true })} total outstanding`"
            :icon="CalendarClock"
            :tone="f.overdue > 0 ? 'danger' : 'success'"
            :loading="store.loading"
            to="/finance/receivables"
          />
        </template>
        <template v-else>
          <StatCard label="Vacant beds" :value="d.occupancy.vacant" :icon="BedDouble" tone="success" to="/rooms/allocate" />
          <StatCard label="Open bookings" :value="d.occupancy.pending_bookings" :icon="CalendarClock" tone="warning" to="/bookings" />
        </template>
      </section>

      <section v-if="f" class="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="Financial metrics">
        <StatCard label="Invoiced" :value="formatCurrency(f.invoiced, { compact: f.invoiced >= 1e6 })" :icon="CreditCard" :loading="store.loading" to="/rent/invoices" />
        <StatCard label="Expenses" :value="formatCurrency(f.expenses, { compact: f.expenses >= 1e6 })" :hint="`${formatCurrency(f.unpaid_expenses, { compact: true })} unpaid`" :icon="Wallet" tone="warning" :loading="store.loading" to="/expenses" />
        <StatCard label="Net cash flow" :value="formatCurrency(f.net, { compact: Math.abs(f.net) >= 1e6 })" hint="Collected − expenses" :icon="TrendingDown" :tone="f.net >= 0 ? 'success' : 'danger'" :loading="store.loading" to="/finance/reports" />
        <StatCard label="Open bookings" :value="d.occupancy.pending_bookings" :hint="`${d.occupancy.vacant} beds vacant`" :icon="CalendarClock" tone="info" :loading="store.loading" to="/bookings" />
      </section>

      <div class="mt-5 grid gap-5 xl:grid-cols-3">
        <Card v-if="d.trend" class="xl:col-span-2">
          <CardHeader>
            <div><CardTitle>Revenue trend</CardTitle><CardDescription>Last 12 months</CardDescription></div>
          </CardHeader>
          <CardContent class="pt-2">
            <RevenueChart :months="d.trend.months" :invoiced="d.trend.invoiced" :collected="d.trend.collected" :expenses="d.trend.expenses" />
          </CardContent>
        </Card>
        <Card :class="!d.trend && 'xl:col-span-3'">
          <CardHeader><div><CardTitle>Bed vacancy</CardTitle><CardDescription>{{ d.occupancy.total_beds }} beds across {{ Object.values(d.occupancy.rooms).reduce((a, b) => a + b, 0) }} rooms</CardDescription></div></CardHeader>
          <CardContent>
            <VacancyBar v-bind="d.occupancy" />
            <Button v-if="d.occupancy.vacant && auth.can('PG Occupancy', 'create')" variant="outline" class="mt-5 w-full" as-child>
              <RouterLink to="/rooms/allocate">Allocate a vacant bed</RouterLink>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        <Card v-if="d.upcoming_dues">
          <CardHeader>
            <div><CardTitle>Upcoming rent</CardTitle><CardDescription>Due within 7 days or overdue</CardDescription></div>
            <Button variant="link" size="sm" class="px-0" as-child><RouterLink to="/finance/receivables">View all</RouterLink></Button>
          </CardHeader>
          <CardContent class="pt-2"><UpcomingDues :rows="d.upcoming_dues" /></CardContent>
        </Card>
        <Card v-if="d.recent_transactions">
          <CardHeader>
            <div><CardTitle>Recent transactions</CardTitle></div>
            <Button variant="link" size="sm" class="px-0" as-child><RouterLink to="/payments">View all</RouterLink></Button>
          </CardHeader>
          <CardContent class="pt-2"><RecentTransactions :rows="d.recent_transactions" /></CardContent>
        </Card>
        <Card v-if="d.expense_by_category">
          <CardHeader><div><CardTitle>Expenses by category</CardTitle><CardDescription>Selected period</CardDescription></div></CardHeader>
          <CardContent class="pt-2"><ExpenseChart :data="d.expense_by_category" /></CardContent>
        </Card>
        <Card v-if="d.property_comparison.length > 1 || !d.finance">
          <CardHeader><div><CardTitle>Property comparison</CardTitle><CardDescription>Occupancy{{ f ? ' and collections' : '' }}</CardDescription></div></CardHeader>
          <CardContent class="pt-1"><PropertyComparison :rows="d.property_comparison" :show-revenue="!!f" /></CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>
