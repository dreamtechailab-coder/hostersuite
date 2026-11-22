import { api } from './api'
import { resource } from './resource.service'
import type { Invoice, Meter, MeterReading } from '@/types'

export interface RentSummary {
  period: { start: string; end: string }
  totals: { invoiced: number; collected: number; outstanding: number; invoices: number }
  by_status: { status: string; count: number; outstanding: number }[]
  overdue: { count: number; amount: number }
  pending_occupancies: number
}
export interface InvoiceDetails {
  invoice: Invoice
  payments: { name: string; payment_date: string; mode: string; reference_no?: string; allocated_amount: number }[]
  tenant: { full_name: string; mobile: string; email?: string }
  room_number?: string
  property: { property_name: string; address_line?: string; city?: string; phone?: string }
}

export const rentService = {
  summary: (property?: string, month?: string) =>
    api.pgGet<{ data: RentSummary }>('rent.get_rent_summary', { property, month }).then((r) => r.data),
  list: (params = {}) => resource.list<Invoice>('PG Rent Invoice', params),
  get: (name: string) => api.pgGet<{ data: InvoiceDetails }>('rent.get_invoice', { name }).then((r) => r.data),
  generate: (month: string, property?: string) =>
    api.pgPost<{ data: { created: string[]; skipped: number; errors: { occupancy: string; error: string }[] }; message: string }>(
      'rent.generate_invoices',
      { month, property },
    ),
  createForOccupancy: (occupancy: string, month?: string) =>
    api.pgPost<{ data: Invoice; message: string }>('rent.create_invoice_for_occupancy', { occupancy, month }),
  cancel: (name: string) => resource.cancel<Invoice>('PG Rent Invoice', name),
  sendWhatsApp: (name: string, purpose: 'Rent Reminder' | 'Invoice Issued' = 'Rent Reminder') =>
    api.pgPost<{ message: string }>('rent.send_invoice_whatsapp', { name, purpose }),
}

export interface ElectricitySummary {
  units: number
  amount: number
  readings: number
  unbilled_amount: number
  active_meters: number
  pending_readings: number
  trend: { month: string; units: number; amount: number }[]
}
export const electricityService = {
  meters: (property?: string, month?: string) =>
    api.pgGet<{ data: Meter[] }>('electricity.get_meters', { property, month }).then((r) => r.data),
  summary: (property?: string, month?: string) =>
    api.pgGet<{ data: ElectricitySummary }>('electricity.get_summary', { property, month }).then((r) => r.data),
  saveMeter: (data: Partial<Meter>) => resource.save<Meter>('PG Electricity Meter', data),
  readings: (params = {}) => resource.list<MeterReading>('PG Meter Reading', params),
  preview: (payload: { meter: string; current_reading: number; reading_date?: string; period_start?: string; period_end?: string }) =>
    api.pgPost<{ data: MeterReading }>('electricity.preview_reading', payload).then((r) => r.data),
  record: (payload: { meter: string; current_reading: number; reading_date?: string; period_start?: string; period_end?: string }) =>
    api.pgPost<{ data: MeterReading; message: string }>('electricity.record_reading', payload),
  bills: (params: { property?: string; billing_status?: string; page?: number; page_size?: number }) =>
    api.pgGet<{ data: (MeterReading & { room_number: string })[]; total: number; page: number; page_size: number }>(
      'electricity.get_bills',
      params,
    ),
  cancelReading: (name: string) => resource.cancel<MeterReading>('PG Meter Reading', name),
}
