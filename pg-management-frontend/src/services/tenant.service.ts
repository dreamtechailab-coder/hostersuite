import { api } from './api'
import { resource } from './resource.service'
import type { Booking, Invoice, Occupancy, Payment, Tenant } from '@/types'

export interface TenantDetails {
  tenant: Tenant
  occupancies: Occupancy[]
  bookings: Booking[]
  invoices?: Invoice[]
  payments?: Payment[]
  balance?: number
}

export const tenantService = {
  list: (params = {}) => resource.list<Tenant>('PG Tenant', params),
  get: (name: string) => resource.get<Tenant>('PG Tenant', name),
  save: (data: Partial<Tenant>) => resource.save<Tenant>('PG Tenant', data),
  remove: (name: string) => resource.remove('PG Tenant', name),
  details: (name: string) => api.pgGet<{ data: TenantDetails }>('tenant.get_tenant_details', { name }).then((r) => r.data),
}

export const bookingService = {
  list: (params = {}) => resource.list<Booking>('PG Booking', params),
  save: (data: Partial<Booking>) => resource.save<Booking>('PG Booking', data),
  confirm: (name: string) => api.pgPost<{ data: Booking; message: string }>('tenant.confirm_booking', { name }),
  cancel: (name: string, reason?: string) => api.pgPost<{ data: Booking; message: string }>('tenant.cancel_booking', { name, reason }),
}

export interface CheckInPayload {
  tenant: string
  bed: string
  check_in_date?: string
  monthly_rent?: number | null
  security_deposit?: number | null
  rent_due_day?: number | null
  booking?: string
  generate_invoice?: number
}
export const occupancyService = {
  list: (params = {}) => resource.list<Occupancy>('PG Occupancy', params),
  save: (data: Partial<Occupancy>) => resource.save<Occupancy>('PG Occupancy', data),
  checkIn: (payload: CheckInPayload) =>
    api.pgPost<{ data: { occupancy: Occupancy; invoice?: string }; message: string }>('tenant.check_in', { ...payload }),
  giveNotice: (name: string, notice_date?: string, expected_check_out?: string) =>
    api.pgPost<{ message: string }>('tenant.give_notice', { name, notice_date, expected_check_out }),
  checkOut: (payload: { name: string; check_out_date?: string; deposit_status: string; deposit_refund_amount?: number; generate_final_invoice?: number }) =>
    api.pgPost<{ data: { invoice?: string }; message: string }>('tenant.check_out', payload),
}
