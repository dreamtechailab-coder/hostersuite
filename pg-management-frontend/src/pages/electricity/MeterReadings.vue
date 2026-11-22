<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Gauge, Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import MeterFormDialog from '@/components/electricity/MeterFormDialog.vue'
import ReadingDialog from '@/components/electricity/ReadingDialog.vue'
import { electricityService } from '@/services/rent.service'
import { useAsync } from '@/composables/useAsync'
import { useResourceList } from '@/composables/useResourceList'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { formatNumber } from '@/utils/currency'
import type { Meter, MeterReading } from '@/types'

const route = useRoute()
const property = usePropertyStore()
const { can } = usePermissions()
const tab = ref('readings')
const meters = useAsync(() => electricityService.meters(property.filter))
watch(() => property.filter, () => meters.run(), { immediate: true })
const readings = useResourceList<MeterReading>('PG Meter Reading', { filters: () => ({ docstatus: 1 }) })
const meterOpen = ref(false)
const readingOpen = ref(false)
const sel = ref<Meter | null>(null)
onMounted(() => {
  if (route.query.addMeter) meterOpen.value = true
})
watch(() => meters.data.value, (list) => {
  const q = route.query.meter as string
  const m = q && list?.find((x) => x.name === q)
  if (m) record(m)
})
function record(m: Meter) {
  sel.value = m
  readingOpen.value = true
}
function refresh() {
  meters.run()
  readings.reload()
}
</script>

<template>
  <div>
    <PageHeader title="Meter readings" back="/electricity">
      <template #actions>
        <Button v-if="can('PG Electricity Meter', 'create')" variant="outline" @click="meterOpen = true"><Plus />Add meter</Button>
      </template>
    </PageHeader>
    <Tabs v-model="tab">
      <TabsList>
        <TabsTrigger value="readings">Readings</TabsTrigger>
        <TabsTrigger value="meters">Meters</TabsTrigger>
      </TabsList>
      <TabsContent value="readings">
        <DataTable
          :columns="[
            { key: 'reading_date', label: 'Date', format: 'date' },
            { key: 'meter', label: 'Meter' },
            { key: 'room', label: 'Room', mobileHidden: true },
            { key: 'current_reading', label: 'Reading', format: 'number', align: 'right' },
            { key: 'units_consumed', label: 'Units', format: 'number', align: 'right' },
            { key: 'amount', label: 'Amount', format: 'currency', align: 'right' },
            { key: 'billing_status', label: 'Billing', format: 'status' },
          ]"
          :rows="readings.rows.value"
          :loading="readings.loading.value"
          :error="readings.error.value"
          empty-title="No readings recorded"
          :pagination="{ page: readings.page.value, pageCount: readings.pageCount.value, total: readings.total.value, from: readings.from.value, to: readings.to.value }"
          @update:page="readings.setPage"
          @retry="readings.reload"
        />
      </TabsContent>
      <TabsContent value="meters">
        <DataTable
          :columns="[
            { key: 'meter_number', label: 'Meter' },
            { key: 'room_number', label: 'Room' },
            { key: 'rate_per_unit', label: 'Rate/unit', format: 'currency', align: 'right' },
            { key: 'last_reading', label: 'Last reading', align: 'right' },
            { key: 'last_reading_date', label: 'On', format: 'date' },
          ]"
          :rows="meters.data.value || []"
          :loading="meters.loading.value"
          :error="meters.error.value"
          empty-title="No meters"
          @retry="meters.run"
        >
          <template #cell-last_reading="{ value }"><span class="tabular">{{ formatNumber(value, 2) }}</span></template>
          <template v-if="can('PG Meter Reading', 'create')" #row-actions="{ row }">
            <Button size="sm" variant="outline" :disabled="!row.is_active" @click="record(row)"><Gauge />Reading</Button>
          </template>
        </DataTable>
      </TabsContent>
    </Tabs>
    <MeterFormDialog v-model:open="meterOpen" @saved="refresh" />
    <ReadingDialog v-model:open="readingOpen" :meter="sel" @saved="refresh" />
  </div>
</template>
