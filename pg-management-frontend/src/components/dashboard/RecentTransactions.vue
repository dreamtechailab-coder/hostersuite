<script setup lang="ts">
import { ArrowDownLeft, ArrowUpRight } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/date'

defineProps<{ rows: { type: 'Payment' | 'Expense'; name: string; party: string; date: string; amount: number; detail: string }[] }>()
</script>

<template>
  <EmptyState v-if="!rows.length" compact title="No transactions yet" />
  <ul v-else class="divide-y">
    <li v-for="t in rows" :key="t.type + t.name">
      <RouterLink :to="t.type === 'Payment' ? `/payments/${t.name}` : `/expenses/${t.name}/edit`" class="-mx-2 flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-muted/40">
        <span :class="['flex size-9 shrink-0 items-center justify-center rounded-full', t.type === 'Payment' ? 'bg-success-soft text-success' : 'bg-danger-soft text-destructive']">
          <ArrowDownLeft v-if="t.type === 'Payment'" class="size-4" /><ArrowUpRight v-else class="size-4" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm font-medium">{{ t.party }}</span>
          <span class="block truncate text-xs text-muted-foreground">{{ t.detail }} · {{ formatDate(t.date, { day: 'numeric', month: 'short' }) }}</span>
        </span>
        <span :class="['tabular text-sm font-semibold', t.type === 'Payment' ? 'text-success' : '']">
          {{ t.type === 'Payment' ? '+' : '−' }}{{ formatCurrency(t.amount) }}
        </span>
      </RouterLink>
    </li>
  </ul>
</template>
