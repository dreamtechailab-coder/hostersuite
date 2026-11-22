<script setup lang="ts">
import { BellRing } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { Button } from '@/components/ui/button'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatCurrency } from '@/utils/currency'
import { dueLabel, daysBetween, today } from '@/utils/date'
import { rentService } from '@/services/rent.service'
import { useMutation } from '@/composables/useMutation'
import { useAuthStore } from '@/stores/auth'

defineProps<{ rows: { name: string; tenant: string; tenant_name: string; due_date: string; outstanding_amount: number; status: string }[] }>()
const auth = useAuthStore()
const remind = useMutation((name: string) => rentService.sendWhatsApp(name, 'Rent Reminder'))
const overdue = (d: string) => daysBetween(today(), d) < 0
</script>

<template>
  <EmptyState v-if="!rows.length" compact title="No dues in the next 7 days" description="You're all caught up on collections." />
  <ul v-else class="divide-y">
    <li v-for="r in rows" :key="r.name" class="flex items-center gap-3 py-2.5">
      <RouterLink :to="`/rent/invoices/${r.name}`" class="min-w-0 flex-1">
        <span class="block truncate text-sm font-medium">{{ r.tenant_name }}</span>
        <span :class="['block text-xs', overdue(r.due_date) ? 'font-medium text-destructive' : 'text-muted-foreground']">{{ dueLabel(r.due_date) }}</span>
      </RouterLink>
      <span class="tabular text-sm font-semibold">{{ formatCurrency(r.outstanding_amount) }}</span>
      <Button
        v-if="auth.settings?.whatsapp_enabled && auth.can('PG WhatsApp Message', 'create')"
        variant="ghost"
        size="icon-sm"
        :aria-label="`Send reminder to ${r.tenant_name}`"
        :disabled="remind.pending.value"
        @click="remind.run(r.name)"
      >
        <BellRing />
      </Button>
    </li>
  </ul>
</template>
