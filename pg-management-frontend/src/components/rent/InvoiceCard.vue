<script setup lang="ts">
import { RouterLink } from 'vue-router'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currency'
import { dueLabel, formatMonth } from '@/utils/date'
import type { Invoice } from '@/types'

defineProps<{ invoice: Invoice }>()
</script>

<template>
  <RouterLink :to="`/rent/invoices/${invoice.name}`" class="flex items-center gap-3 rounded-xl border bg-card p-4 shadow-xs transition hover:border-primary/30">
    <div class="min-w-0 flex-1">
      <p class="truncate font-medium">{{ invoice.tenant_name }}</p>
      <p class="truncate text-xs text-muted-foreground">{{ formatMonth(invoice.period_start) }} · {{ invoice.name }}</p>
      <p v-if="invoice.outstanding_amount > 0" class="mt-1 text-xs" :class="invoice.status === 'Overdue' ? 'text-destructive' : 'text-muted-foreground'">{{ dueLabel(invoice.due_date) }}</p>
    </div>
    <div class="text-right">
      <p class="tabular font-semibold">{{ formatCurrency(invoice.outstanding_amount > 0 ? invoice.outstanding_amount : invoice.total_amount) }}</p>
      <StatusBadge :status="invoice.status" class="mt-1" />
    </div>
  </RouterLink>
</template>
