<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Banknote, CreditCard, Landmark, Smartphone, FileCheck } from 'lucide-vue-next'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/date'
import type { Payment } from '@/types'

defineProps<{ payment: Payment }>()
const ICONS = { Cash: Banknote, UPI: Smartphone, 'Bank Transfer': Landmark, Card: CreditCard, Cheque: FileCheck }
</script>

<template>
  <RouterLink :to="`/payments/${payment.name}`" class="flex items-center gap-3 px-4 py-3.5 active:bg-muted/60">
    <span :class="['flex size-10 shrink-0 items-center justify-center rounded-full', payment.docstatus === 2 ? 'bg-muted text-muted-foreground' : 'bg-success-soft text-success']">
      <component :is="ICONS[payment.mode] || Banknote" class="size-4" />
    </span>
    <span class="min-w-0 flex-1">
      <span class="block truncate font-medium">{{ payment.tenant_name }}</span>
      <span class="block truncate text-xs text-muted-foreground">{{ formatDate(payment.payment_date) }} · {{ payment.mode }}<template v-if="payment.reference_no"> · {{ payment.reference_no }}</template></span>
    </span>
    <span :class="['tabular font-semibold', payment.docstatus === 2 ? 'text-muted-foreground line-through' : 'text-success']">{{ formatCurrency(payment.amount) }}</span>
  </RouterLink>
</template>
