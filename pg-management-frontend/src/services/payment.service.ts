import { api } from './api'
import { resource } from './resource.service'
import type { Expense, Invoice, Payment, PaymentMode } from '@/types'

export interface CollectPayload {
  tenant: string
  amount: number
  mode: PaymentMode
  payment_date?: string
  reference_no?: string
  remarks?: string
  allocations?: { invoice: string; allocated_amount: number }[]
  client_request_id: string
}

export const paymentService = {
  list: (params = {}) => resource.list<Payment>('PG Payment', params),
  outstanding: (tenant: string) =>
    api.pgGet<{ data: Invoice[] }>('payment.get_outstanding_invoices', { tenant }).then((r) => r.data),
  collect: (payload: CollectPayload) => api.pgPost<{ data: Payment; message: string }>('payment.collect_payment', { ...payload }),
  get: (name: string) =>
    api
      .pgGet<{ data: { payment: Payment; tenant: { full_name: string; mobile: string }; received_by_name?: string } }>(
        'payment.get_payment',
        { name },
      )
      .then((r) => r.data),
  cancel: (name: string, reason?: string) => api.pgPost<{ message: string }>('payment.cancel_payment', { name, reason }),
}

export const expenseService = {
  list: (params = {}) => resource.list<Expense>('PG Expense', params),
  get: (name: string) => resource.get<Expense>('PG Expense', name),
  save: (data: Partial<Expense>) => resource.save<Expense>('PG Expense', data),
  remove: (name: string) => resource.remove('PG Expense', name),
  markPaid: (name: string, paid_on?: string, payment_mode?: string) =>
    api.pgPost<{ message: string }>('expense.mark_paid', { name, paid_on, payment_mode }),
  summary: (property?: string, from_date?: string, to_date?: string) =>
    api
      .pgGet<{ data: { totals: { total: number; unpaid: number; count: number }; by_category: { name: string; value: number; count: number }[] } }>(
        'expense.get_summary',
        { property, from_date, to_date },
      )
      .then((r) => r.data),
  categories: () => resource.options('PG Expense Category', { limit: 200 }),
}
