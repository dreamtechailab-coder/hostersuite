import { api } from './api'
import type { NamedValue } from '@/types'

type Range = { property?: string; from_date?: string; to_date?: string }

export interface DashboardData {
  range: { from: string; to: string }
  can_finance: boolean
  occupancy: {
    total_beds: number
    occupied: number
    reserved: number
    vacant: number
    maintenance: number
    rate: number
    rooms: Record<string, number>
    active_tenants: number
    on_notice: number
    check_ins: number
    pending_bookings: number
  }
  property_comparison: { property: string; property_name: string; beds: number; occupied: number; vacant: number; collected?: number }[]
  finance?: {
    invoiced: number
    collected: number
    collection_rate: number
    outstanding: number
    overdue: number
    expenses: number
    unpaid_expenses: number
    net: number
  }
  trend?: { months: string[]; invoiced: number[]; collected: number[]; expenses: number[] }
  expense_by_category?: NamedValue[]
  recent_transactions?: { type: 'Payment' | 'Expense'; name: string; party: string; date: string; amount: number; detail: string }[]
  upcoming_dues?: { name: string; tenant: string; tenant_name: string; room: string; due_date: string; outstanding_amount: number; status: string }[]
}

export interface ReceivableRow {
  tenant: string
  tenant_name: string
  property: string
  mobile: string
  tenant_status: string
  invoices: number
  outstanding: number
  current_due: number
  d1_30: number
  d31_60: number
  d61_90: number
  d90_plus: number
  oldest_due: string
}

export const reportService = {
  dashboard: (p: Range) => api.pgGet<{ data: DashboardData }>('dashboard.get_dashboard', p).then((r) => r.data),
  occupancy: (p: Range) =>
    api
      .pgGet<{
        data: {
          by_property: { property: string; property_name: string; beds: number; occupied: number; reserved: number; vacant: number; maintenance: number; rate: number }[]
          by_room_type: { room_type: string; beds: number; occupied: number; avg_rent: number; rate: number }[]
          movement: { m: string; check_ins: number; check_outs: number }[]
          average_stay_days: number
          range: { from: string; to: string }
        }
      }>('report.occupancy_report', p)
      .then((r) => r.data),
  revenue: (p: Range) =>
    api
      .pgGet<{
        data: {
          monthly: { month: string; property: string; invoiced: number; collected: number; outstanding: number; invoices: number }[]
          by_type: NamedValue[]
          by_mode: NamedValue[]
          totals: { invoiced: number; collected: number; outstanding: number }
          range: { from: string; to: string }
        }
      }>('report.revenue_report', p)
      .then((r) => r.data),
  expense: (p: Range) =>
    api
      .pgGet<{
        data: {
          by_category: NamedValue[]
          monthly: { month: string; amount: number }[]
          by_property: { property: string; amount: number }[]
          top_vendors: NamedValue[]
          total: number
          range: { from: string; to: string }
        }
      }>('report.expense_report', p)
      .then((r) => r.data),
  receivables: (property?: string, search?: string) =>
    api
      .pgGet<{ data: { rows: ReceivableRow[]; totals: Record<string, number> } }>('finance.get_receivables', { property, search })
      .then((r) => r.data),
  payables: (property?: string) =>
    api
      .pgGet<{
        data: {
          expenses: { name: string; property: string; category: string; vendor?: string; amount: number; expense_date: string; due_date?: string; description?: string }[]
          deposits_due: { name: string; tenant: string; tenant_name: string; property: string; check_out_date: string; security_deposit: number }[]
          totals: { unpaid_expenses: number; overdue_expenses: number; deposits_to_refund: number; deposits_held: number }
        }
      }>('finance.get_payables', { property })
      .then((r) => r.data),
  financialSummary: (property?: string, year?: number) =>
    api
      .pgGet<{
        data: {
          year: number
          months: { month: number; invoiced: number; collected: number; expenses: number; net: number }[]
          totals: { invoiced: number; collected: number; expenses: number; net: number }
          income_by_type: NamedValue[]
          expense_by_category: NamedValue[]
        }
      }>('finance.get_financial_summary', { property, year })
      .then((r) => r.data),
}
