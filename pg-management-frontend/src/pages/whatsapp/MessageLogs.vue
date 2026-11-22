<script setup lang="ts">
import { ref } from 'vue'
import { RotateCw } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import FilterPanel from '@/components/common/FilterPanel.vue'
import DataTable from '@/components/common/DataTable.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { whatsappService } from '@/services/whatsapp.service'
import { useResourceList } from '@/composables/useResourceList'
import { useFilters } from '@/composables/useFilters'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { formatDateTime } from '@/utils/date'
import type { WhatsAppMessage } from '@/types'

const { can } = usePermissions()
const { filters, activeCount, reset } = useFilters({ status: '' })
const list = useResourceList<WhatsAppMessage>('PG WhatsApp Message', { filters: () => ({ status: filters.status }), orderBy: 'creation desc' })
const sel = ref<WhatsAppMessage | null>(null)
const open = ref(false)
const retry = useMutation(whatsappService.retry)
async function onRetry(m: WhatsAppMessage) {
  if (await retry.run(m.name)) list.reload()
}
</script>

<template>
  <div>
    <PageHeader title="Message logs" back="/whatsapp" />
    <div class="mb-4">
      <FilterPanel :active-count="activeCount" @reset="reset">
        <template #search><SearchInput v-model="list.search.value" placeholder="Mobile or text…" /></template>
        <NativeSelect v-model="filters.status" :options="['Sent', 'Queued', 'Failed']" placeholder="All statuses" class="lg:w-40" />
      </FilterPanel>
    </div>
    <DataTable
      :columns="[
        { key: 'creation', label: 'When' },
        { key: 'mobile', label: 'To' },
        { key: 'template', label: 'Template' },
        { key: 'message', label: 'Message', mobileHidden: true },
        { key: 'status', label: 'Status', format: 'status' },
      ]"
      :rows="list.rows.value"
      :loading="list.loading.value"
      :error="list.error.value"
      clickable
      empty-title="No messages yet"
      :pagination="{ page: list.page.value, pageCount: list.pageCount.value, total: list.total.value, from: list.from.value, to: list.to.value }"
      @update:page="list.setPage"
      @row-click="(r) => ((sel = r), (open = true))"
      @retry="list.reload"
    >
      <template #cell-creation="{ value }">{{ formatDateTime(value) }}</template>
      <template #cell-template="{ value }">{{ value || 'Custom' }}</template>
      <template #cell-message="{ value }"><span class="line-clamp-1 max-w-sm text-muted-foreground">{{ value }}</span></template>
      <template v-if="can('PG WhatsApp Message', 'create')" #row-actions="{ row }">
        <Button v-if="row.status === 'Failed'" size="sm" variant="ghost" @click="onRetry(row)"><RotateCw />Retry</Button>
      </template>
    </DataTable>
    <ModalDialog v-model:open="open" title="Message" :description="sel ? `${sel.mobile} · ${formatDateTime(sel.creation)}` : ''">
      <template v-if="sel">
        <StatusBadge :status="sel.status" />
        <p class="mt-3 whitespace-pre-line rounded-lg bg-muted/50 p-3 text-sm">{{ sel.message }}</p>
        <p v-if="sel.error" class="mt-3 rounded-lg bg-danger-soft p-3 text-sm text-destructive">{{ sel.error }}</p>
        <p v-if="sel.reference_name" class="mt-3 text-xs text-muted-foreground">Related to {{ sel.reference_doctype }} {{ sel.reference_name }}</p>
      </template>
    </ModalDialog>
  </div>
</template>
