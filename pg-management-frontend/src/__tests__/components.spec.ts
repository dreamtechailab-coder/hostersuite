import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusBadge from '@/components/common/StatusBadge.vue'
import DataTable from '@/components/common/DataTable.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { ApiError } from '@/services/api'
import { setCurrency } from '@/utils/currency'

describe('StatusBadge', () => {
  it.each([
    ['Paid', 'text-success'],
    ['Overdue', 'text-destructive'],
    ['Unpaid', 'text-warning'],
    ['Reserved', 'text-info'],
  ])('maps %s to the semantic colour', (status, cls) => {
    const w = mount(StatusBadge, { props: { status } })
    expect(w.text()).toBe(status)
    expect(w.html()).toContain(cls)
  })
})

describe('DataTable', () => {
  const columns = [
    { key: 'tenant_name', label: 'Tenant' },
    { key: 'amount', label: 'Amount', format: 'currency' as const },
    { key: 'status', label: 'Status', format: 'status' as const },
  ]
  it('renders rows with formatted cells and emits row-click', async () => {
    setCurrency('INR')
    const w = mount(DataTable, {
      props: { columns, rows: [{ name: 'A', tenant_name: 'Ravi', amount: 9000, status: 'Paid' }], clickable: true },
    })
    expect(w.text()).toContain('Ravi')
    expect(w.text()).toContain('₹9,000')
    await w.find('tbody tr').trigger('click')
    expect(w.emitted('row-click')?.[0]).toEqual([{ name: 'A', tenant_name: 'Ravi', amount: 9000, status: 'Paid' }])
  })
  it('shows empty and error states', () => {
    const empty = mount(DataTable, { props: { columns, rows: [], emptyTitle: 'No invoices' } })
    expect(empty.findComponent(EmptyState).text()).toContain('No invoices')
    const err = mount(DataTable, { props: { columns, rows: [], error: new ApiError('nope', 403, 'PermissionError') } })
    expect(err.findComponent(ErrorState).text()).toContain('No access')
  })
})
