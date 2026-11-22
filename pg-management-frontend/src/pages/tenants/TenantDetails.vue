<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CreditCard, LogIn, LogOut, MessageCircle, Pencil, Phone, Mail, CalendarClock, ShieldCheck, FileText, MoreHorizontal } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Avatar } from '@/components/ui/avatar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import DetailList from '@/components/common/DetailList.vue'
import DataTable from '@/components/common/DataTable.vue'
import Money from '@/components/common/Money.vue'
import CheckInDialog from '@/components/occupancy/CheckInDialog.vue'
import CheckOutDialog from '@/components/occupancy/CheckOutDialog.vue'
import SendWhatsAppDialog from '@/components/whatsapp/SendWhatsAppDialog.vue'
import { useTenantStore } from '@/stores/tenant'
import { usePermissions } from '@/composables/usePermissions'
import { useAuthStore } from '@/stores/auth'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/date'
import type { TenantDetails } from '@/services/tenant.service'

const props = defineProps<{ name: string }>()
const router = useRouter()
const store = useTenantStore()
const auth = useAuthStore()
const { can } = usePermissions()
const data = ref<TenantDetails | null>(null)
const loading = ref(true)
const error = ref<Error | null>(null)
const tab = ref('overview')
async function load(force = false) {
  loading.value = true
  error.value = null
  try {
    data.value = await store.fetchDetails(props.name, force)
  } catch (e) {
    error.value = e as Error
  } finally {
    loading.value = false
  }
}
onMounted(() => load())
const reload = () => load(true)
const t = computed(() => data.value?.tenant)
const current = computed(() => data.value?.occupancies.find((o) => o.status !== 'Ended') || null)
const openBooking = computed(() => data.value?.bookings.find((b) => b.status === 'Confirmed' || b.status === 'Pending'))
const checkInOpen = ref(false)
const outOpen = ref(false)
const outMode = ref<'notice' | 'checkout'>('checkout')
const waOpen = ref(false)
function openOut(mode: 'notice' | 'checkout') {
  outMode.value = mode
  outOpen.value = true
}
function onDone() {
  store.invalidate(props.name)
  reload()
}
</script>

<template>
  <div>
    <ErrorState v-if="error" :error="error" @retry="reload" />
    <LoadingSkeleton v-else-if="loading && !data" variant="detail" />
    <template v-else-if="data && t">
      <PageHeader :title="t.full_name" back="/tenants">
        <template #badge><StatusBadge :status="t.status" /></template>
        <template #description>
          <span class="inline-flex flex-wrap gap-x-4 gap-y-1">
            <a :href="`tel:${t.mobile}`" class="inline-flex items-center gap-1 hover:text-foreground"><Phone class="size-3.5" />{{ t.mobile }}</a>
            <a v-if="t.email" :href="`mailto:${t.email}`" class="inline-flex items-center gap-1 hover:text-foreground"><Mail class="size-3.5" />{{ t.email }}</a>
          </span>
        </template>
        <template #actions>
          <Button v-if="current && can('PG Payment', 'create')" as-child><RouterLink :to="{ path: '/payments/collect', query: { tenant: t.name } }"><CreditCard />Collect</RouterLink></Button>
          <Button v-if="!current && can('PG Occupancy', 'create')" @click="checkInOpen = true"><LogIn />Check in</Button>
          <DropdownMenu>
            <DropdownMenuTrigger as-child><Button variant="outline" size="icon" aria-label="More actions"><MoreHorizontal /></Button></DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem v-if="can('PG Tenant', 'write')" @select="router.push(`/tenants/${t.name}/edit`)"><Pencil />Edit details</DropdownMenuItem>
              <DropdownMenuItem v-if="auth.settings?.whatsapp_enabled && t.whatsapp_opt_in && can('PG WhatsApp Message', 'create')" @select="waOpen = true"><MessageCircle />Send WhatsApp</DropdownMenuItem>
              <DropdownMenuItem v-if="current?.status === 'Active' && can('PG Occupancy', 'write')" @select="openOut('notice')"><CalendarClock />Record notice</DropdownMenuItem>
              <DropdownMenuItem v-if="current && can('PG Occupancy', 'write')" destructive @select="openOut('checkout')"><LogOut />Check out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </template>
      </PageHeader>

      <div class="mb-5 grid gap-3 sm:grid-cols-3">
        <Card class="flex-row items-center gap-4 p-4">
          <Avatar :name="t.full_name" :src="t.photo" class="size-12" />
          <div class="min-w-0">
            <p class="text-xs text-muted-foreground">Current stay</p>
            <p v-if="current" class="truncate font-semibold">Room {{ current.room_number }} · Bed {{ current.bed_label }}</p>
            <p v-else class="font-semibold text-muted-foreground">Not staying</p>
            <p v-if="current" class="truncate text-xs text-muted-foreground">Since {{ formatDate(current.check_in_date) }}</p>
          </div>
        </Card>
        <Card class="p-4">
          <p class="text-xs text-muted-foreground">Monthly rent</p>
          <p class="tabular text-xl font-semibold">{{ current ? formatCurrency(current.monthly_rent) : '—' }}</p>
          <p v-if="current" class="text-xs text-muted-foreground">Due on day {{ current.rent_due_day }} · deposit {{ formatCurrency(current.security_deposit) }}</p>
        </Card>
        <Card v-if="data.balance !== undefined" class="p-4">
          <p class="text-xs text-muted-foreground">Outstanding balance</p>
          <p :class="['tabular text-xl font-semibold', data.balance > 0 ? 'text-destructive' : 'text-success']">{{ formatCurrency(data.balance) }}</p>
          <p class="text-xs text-muted-foreground">{{ data.balance > 0 ? 'Payment pending' : 'All dues cleared' }}</p>
        </Card>
      </div>

      <div v-if="!current && openBooking" class="mb-5 flex flex-wrap items-center gap-3 rounded-xl border border-info/30 bg-info-soft p-4 text-sm">
        <span class="flex-1">Booking <strong>{{ openBooking.name }}</strong> is {{ openBooking.status.toLowerCase() }} – expected check-in {{ formatDate(openBooking.expected_check_in) }}.</span>
        <Button v-if="can('PG Occupancy', 'create')" size="sm" as-child>
          <RouterLink :to="{ path: '/rooms/allocate', query: { tenant: t.name, booking: openBooking.name } }">Allocate bed</RouterLink>
        </Button>
      </div>

      <Tabs v-model="tab">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="stays">Stays</TabsTrigger>
          <TabsTrigger v-if="data.invoices" value="invoices">Invoices</TabsTrigger>
          <TabsTrigger v-if="data.payments" value="payments">Payments</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" class="grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
            <CardContent>
              <DetailList
                :items="[
                  { label: 'Gender', value: t.gender },
                  { label: 'Date of birth', value: formatDate(t.date_of_birth) },
                  { label: 'Occupation', value: t.occupation },
                  { label: 'Company / College', value: t.organization },
                  { label: 'Property', value: t.property },
                  { label: 'WhatsApp', value: t.whatsapp_opt_in ? 'Opted in' : 'Opted out' },
                ]"
              />
              <p v-if="t.permanent_address" class="mt-4 text-sm"><span class="block text-xs text-muted-foreground">Permanent address</span>{{ t.permanent_address }}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle class="flex items-center gap-2"><ShieldCheck class="size-4" />KYC & emergency</CardTitle></CardHeader>
            <CardContent>
              <DetailList
                :items="[
                  { label: 'ID type', value: t.id_type },
                  { label: 'ID number', value: t.id_number_masked },
                  { label: 'ID document', value: t.has_id_document ? 'On file' : 'Missing', key: 'doc' },
                  { label: 'Verified', value: t.kyc_verified ? 'Yes' : 'No' },
                  { label: 'Emergency contact', value: t.emergency_contact_name },
                  { label: 'Emergency phone', value: t.emergency_contact_phone },
                ]"
              >
                <template #doc="{ item }"><span :class="t.has_id_document ? 'text-success' : 'text-warning'">{{ item.value }}</span></template>
              </DetailList>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="stays">
          <DataTable
            :columns="[
              { key: 'property', label: 'Property' },
              { key: 'room_number', label: 'Room' },
              { key: 'check_in_date', label: 'Check-in', format: 'date' },
              { key: 'check_out_date', label: 'Check-out', format: 'date' },
              { key: 'monthly_rent', label: 'Rent', format: 'currency', align: 'right' },
              { key: 'deposit_status', label: 'Deposit' },
              { key: 'status', label: 'Status', format: 'status' },
            ]"
            :rows="data.occupancies"
            empty-title="No stays yet"
          />
        </TabsContent>
        <TabsContent v-if="data.invoices" value="invoices">
          <DataTable
            :columns="[
              { key: 'name', label: 'Invoice' },
              { key: 'period_start', label: 'Period', format: 'date' },
              { key: 'due_date', label: 'Due', format: 'date' },
              { key: 'total_amount', label: 'Total', format: 'currency', align: 'right' },
              { key: 'outstanding_amount', label: 'Outstanding', align: 'right' },
              { key: 'status', label: 'Status', format: 'status' },
            ]"
            :rows="data.invoices"
            clickable
            empty-title="No invoices yet"
            @row-click="(r) => router.push(`/rent/invoices/${r.name}`)"
          >
            <template #cell-outstanding_amount="{ value }"><Money :value="value" tone="danger" /></template>
            <template #cell-name="{ value }"><span class="inline-flex items-center gap-1.5"><FileText class="size-3.5 text-muted-foreground" />{{ value }}</span></template>
          </DataTable>
        </TabsContent>
        <TabsContent v-if="data.payments" value="payments">
          <DataTable
            :columns="[
              { key: 'name', label: 'Receipt' },
              { key: 'payment_date', label: 'Date', format: 'date' },
              { key: 'mode', label: 'Mode' },
              { key: 'reference_no', label: 'Reference' },
              { key: 'amount', label: 'Amount', format: 'currency', align: 'right' },
            ]"
            :rows="data.payments"
            clickable
            empty-title="No payments yet"
            @row-click="(r) => router.push(`/payments/${r.name}`)"
          />
        </TabsContent>
      </Tabs>

      <CheckInDialog v-model:open="checkInOpen" :tenant="t.name" :tenant-label="t.full_name" :property="t.property" :booking="openBooking?.name" :bed="openBooking?.status === 'Confirmed' ? openBooking.bed : undefined" @done="onDone" />
      <CheckOutDialog v-model:open="outOpen" :occupancy="current ? { ...current, tenant_name: t.full_name } : null" :mode="outMode" @done="onDone" />
      <SendWhatsAppDialog v-model:open="waOpen" :tenant="t.name" :tenant-name="t.full_name" />
    </template>
  </div>
</template>
