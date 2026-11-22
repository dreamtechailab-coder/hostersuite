<script setup lang="ts" generic="T extends Record<string, any>">
import { ArrowDown, ArrowUp, ChevronRight } from 'lucide-vue-next'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { formatCurrency, formatNumber } from '@/utils/currency'
import { formatDate } from '@/utils/date'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'
import LoadingSkeleton from './LoadingSkeleton.vue'
import Pagination from './Pagination.vue'
import StatusBadge from './StatusBadge.vue'

export interface Column {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  format?: 'currency' | 'date' | 'status' | 'number'
  sortable?: boolean
  class?: string
  /** hide from the mobile card body */
  mobileHidden?: boolean
}

const props = withDefaults(
  defineProps<{
    columns: Column[]
    rows: T[]
    loading?: boolean
    error?: Error | null
    rowKey?: string
    clickable?: boolean
    emptyTitle?: string
    emptyDescription?: string
    /** column used as the card title on mobile (default: first column) */
    titleKey?: string
    /** column shown as the card badge on mobile */
    badgeKey?: string
    pagination?: { page: number; pageCount: number; total: number; from: number; to: number }
    sort?: string
  }>(),
  { rowKey: 'name' },
)
const emit = defineEmits<{ 'row-click': [row: T]; 'update:page': [page: number]; 'update:sort': [sort: string]; retry: [] }>()

function display(col: Column, row: T) {
  const v = row[col.key]
  if (v === null || v === undefined || v === '') return '—'
  if (col.format === 'currency') return formatCurrency(v)
  if (col.format === 'date') return formatDate(v)
  if (col.format === 'number') return formatNumber(v, 2)
  return v
}
function toggleSort(col: Column) {
  if (!col.sortable) return
  const [field, dir] = (props.sort || '').split(' ')
  emit('update:sort', field === col.key && dir === 'desc' ? `${col.key} asc` : `${col.key} desc`)
}
const sortDir = (col: Column) => {
  const [field, dir] = (props.sort || '').split(' ')
  return field === col.key ? dir : null
}
const titleCol = () => props.columns.find((c) => c.key === props.titleKey) || props.columns[0]
const badgeCol = () => props.columns.find((c) => c.key === props.badgeKey) || props.columns.find((c) => c.format === 'status')
const bodyCols = () => props.columns.filter((c) => c !== titleCol() && c !== badgeCol() && !c.mobileHidden)
const alignClass = (c: Column) => (c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : '')
</script>

<template>
  <div class="overflow-hidden rounded-xl border bg-card shadow-xs">
    <slot name="toolbar" />
    <ErrorState v-if="error && !loading" :error="error" @retry="emit('retry')" />
    <LoadingSkeleton v-else-if="loading && !rows.length" />
    <template v-else-if="!rows.length">
      <EmptyState :title="emptyTitle || 'No records found'" :description="emptyDescription"><slot name="empty" /></EmptyState>
    </template>
    <template v-else>
      <!-- Desktop / tablet -->
      <div :class="['hidden md:block', loading && 'opacity-60 transition-opacity']">
        <Table>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead v-for="col in columns" :key="col.key" :class="cn(alignClass(col), col.class)" :aria-sort="sortDir(col) ? (sortDir(col) === 'asc' ? 'ascending' : 'descending') : undefined">
                <button v-if="col.sortable" type="button" class="inline-flex items-center gap-1 uppercase hover:text-foreground" @click="toggleSort(col)">
                  {{ col.label }}
                  <ArrowUp v-if="sortDir(col) === 'asc'" class="size-3" />
                  <ArrowDown v-else-if="sortDir(col) === 'desc'" class="size-3" />
                </button>
                <template v-else>{{ col.label }}</template>
              </TableHead>
              <TableHead v-if="$slots['row-actions']" class="w-12"><span class="sr-only">Actions</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="row in rows"
              :key="row[rowKey]"
              :class="clickable && 'cursor-pointer'"
              :tabindex="clickable ? 0 : undefined"
              @click="clickable && emit('row-click', row)"
              @keydown.enter="clickable && emit('row-click', row)"
            >
              <TableCell v-for="col in columns" :key="col.key" :class="cn(alignClass(col), (col.format === 'currency' || col.format === 'number') && 'tabular', col.class)">
                <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                  <StatusBadge v-if="col.format === 'status'" :status="row[col.key]" />
                  <template v-else>{{ display(col, row) }}</template>
                </slot>
              </TableCell>
              <TableCell v-if="$slots['row-actions']" class="text-right" @click.stop>
                <slot name="row-actions" :row="row" />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      <!-- Mobile: card list -->
      <ul :class="['divide-y md:hidden', loading && 'opacity-60']">
        <li v-for="row in rows" :key="row[rowKey]">
          <slot name="mobile-card" :row="row">
            <component
              :is="clickable ? 'button' : 'div'"
              type="button"
              class="flex w-full items-start gap-3 px-4 py-3.5 text-left active:bg-muted/60"
              @click="clickable && emit('row-click', row)"
            >
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-2">
                  <p class="truncate font-medium">
                    <slot :name="`cell-${titleCol().key}`" :row="row" :value="row[titleCol().key]">{{ display(titleCol(), row) }}</slot>
                  </p>
                  <StatusBadge v-if="badgeCol()" :status="row[badgeCol()!.key]" />
                </div>
                <dl class="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-1 text-[13px]">
                  <template v-for="col in bodyCols()" :key="col.key">
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-xs text-muted-foreground">{{ col.label }}</dt>
                      <dd :class="['truncate', (col.format === 'currency' || col.format === 'number') && 'tabular']">
                        <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ display(col, row) }}</slot>
                      </dd>
                    </div>
                  </template>
                </dl>
              </div>
              <ChevronRight v-if="clickable" class="mt-1 size-4 shrink-0 text-muted-foreground" />
            </component>
            <div v-if="$slots['row-actions']" class="flex justify-end gap-2 px-4 pb-3"><slot name="row-actions" :row="row" /></div>
          </slot>
        </li>
      </ul>
      <Pagination v-if="pagination" v-bind="pagination" @update:page="emit('update:page', $event)" />
    </template>
  </div>
</template>
