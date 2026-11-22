// ---------------------------------------------------------------- API envelopes
export interface ListResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}
export interface DataResponse<T> {
  data: T
  message?: string
}
export type Filters = Record<string, unknown>

// ---------------------------------------------------------------- session
export type PgRole = 'PG Admin' | 'PG Manager' | 'PG Accountant' | 'PG Staff' | 'System Manager'
export type PermType = 'read' | 'write' | 'create' | 'delete' | 'submit' | 'cancel'
export type DocType =
  | 'PG Property' | 'PG Building' | 'PG Floor' | 'PG Room' | 'PG Bed' | 'PG Tenant' | 'PG Booking'
  | 'PG Occupancy' | 'PG Rent Invoice' | 'PG Electricity Meter' | 'PG Meter Reading' | 'PG Payment'
  | 'PG Expense' | 'PG Expense Category' | 'PG WhatsApp Template' | 'PG WhatsApp Message' | 'PG Settings'

export interface PropertyRef {
  name: string
  property_name: string
  city?: string
  is_active?: 0 | 1
}
export interface SessionInfo {
  user: string | null
  full_name?: string
  email?: string
  user_image?: string | null
  roles?: PgRole[]
  is_admin?: boolean
  properties?: PropertyRef[]
  can?: Record<DocType, Record<PermType, boolean>>
  csrf_token?: string
  settings?: { organization_name: string; currency: string; whatsapp_enabled: boolean; vapid_public_key?: string }
}

// ---------------------------------------------------------------- documents
export interface BaseDoc {
  name: string
  creation?: string
  modified?: string
  docstatus?: 0 | 1 | 2
}
export interface Property extends BaseDoc {
  property_name: string
  property_code?: string
  property_type?: 'Boys' | 'Girls' | 'Co-living'
  is_active?: 0 | 1
  manager?: string
  phone?: string
  email?: string
  address_line?: string
  city?: string
  state?: string
  pincode?: string
  amenities?: string
  notes?: string
  total_beds?: number
  occupied_beds?: number
}
export interface Building extends BaseDoc {
  property: string
  building_name: string
  is_active?: 0 | 1
  address_line?: string
  notes?: string
}
export interface Floor extends BaseDoc {
  property: string
  building: string
  floor_name: string
  floor_number?: number
}
export type BedStatus = 'Vacant' | 'Occupied' | 'Reserved' | 'Maintenance'
export interface Bed extends BaseDoc {
  room: string
  bed_label: string
  status: BedStatus
  current_tenant?: string | null
  current_occupancy?: string | null
  reserved_booking?: string | null
  tenant_name?: string | null
  tenant_mobile?: string | null
  reserved_for?: string | null
}
export interface Room extends BaseDoc {
  property: string
  building: string
  floor: string
  room_number: string
  room_type: string
  capacity: number
  occupied_beds?: number
  rent_per_bed: number
  security_deposit?: number
  status: 'Available' | 'Full' | 'Maintenance'
  is_ac?: 0 | 1
  attached_bathroom?: 0 | 1
  amenities?: string
  beds?: Bed[]
  building_name?: string
  floor_name?: string
}
export type TenantStatus = 'Prospective' | 'Active' | 'On Notice' | 'Vacated'
export interface Tenant extends BaseDoc {
  full_name: string
  mobile: string
  email?: string
  gender?: string
  property: string
  status: TenantStatus
  date_of_birth?: string
  photo?: string
  occupation?: string
  organization?: string
  permanent_address?: string
  id_type?: string
  id_number?: string // write-only; server returns masked value only
  id_number_masked?: string | null
  has_id_document?: boolean
  id_document?: string
  kyc_verified?: 0 | 1
  emergency_contact_name?: string
  emergency_contact_phone?: string
  whatsapp_opt_in?: 0 | 1
  notes?: string
}
export type BookingStatus = 'Pending' | 'Confirmed' | 'Checked In' | 'Cancelled'
export interface Booking extends BaseDoc {
  tenant: string
  tenant_name?: string
  property: string
  room: string
  bed?: string
  booking_date: string
  expected_check_in: string
  advance_amount?: number
  status: BookingStatus
  occupancy?: string
  notes?: string
}
export interface Occupancy extends BaseDoc {
  tenant: string
  tenant_name?: string
  property: string
  room: string
  bed: string
  status: 'Active' | 'On Notice' | 'Ended'
  check_in_date: string
  notice_date?: string
  expected_check_out?: string
  check_out_date?: string
  monthly_rent: number
  security_deposit?: number
  deposit_status?: string
  rent_due_day?: number
  room_number?: string
  bed_label?: string
}
export type InvoiceStatus = 'Draft' | 'Unpaid' | 'Partially Paid' | 'Paid' | 'Overdue' | 'Cancelled'
export interface InvoiceItem {
  name?: string
  item_type: 'Rent' | 'Electricity' | 'Late Fee' | 'Deposit' | 'Other'
  description?: string
  amount: number
}
export interface Invoice extends BaseDoc {
  tenant: string
  tenant_name?: string
  occupancy: string
  property: string
  room?: string
  invoice_date: string
  period_start: string
  period_end: string
  due_date: string
  items?: InvoiceItem[]
  total_amount: number
  paid_amount: number
  outstanding_amount: number
  status: InvoiceStatus
}
export interface Meter extends BaseDoc {
  property: string
  room: string
  room_number?: string
  meter_number: string
  rate_per_unit: number
  initial_reading?: number
  last_reading?: number
  last_reading_date?: string
  is_active?: 0 | 1
  reading_this_month?: string | null
}
export interface ElectricityShare {
  tenant: string
  tenant_name?: string
  occupancy?: string
  days: number
  amount: number
  invoice?: string | null
}
export interface MeterReading extends BaseDoc {
  meter: string
  property: string
  room: string
  room_number?: string
  reading_date: string
  period_start: string
  period_end: string
  previous_reading: number
  current_reading: number
  units_consumed: number
  rate_per_unit: number
  amount: number
  billing_status: 'Unbilled' | 'Partially Billed' | 'Billed'
  shares?: ElectricityShare[]
}
export type PaymentMode = 'Cash' | 'UPI' | 'Bank Transfer' | 'Card' | 'Cheque'
export interface PaymentAllocation {
  invoice: string
  allocated_amount: number
  period_start?: string
  total_amount?: number
  outstanding_amount?: number
  status?: InvoiceStatus
}
export interface Payment extends BaseDoc {
  tenant: string
  tenant_name?: string
  property: string
  payment_date: string
  amount: number
  mode: PaymentMode
  reference_no?: string
  allocations?: PaymentAllocation[]
  allocated_amount?: number
  unallocated_amount?: number
  remarks?: string
  received_by?: string
}
export interface Expense extends BaseDoc {
  property: string
  category: string
  expense_date: string
  amount: number
  vendor?: string
  payment_status: 'Paid' | 'Unpaid'
  due_date?: string
  paid_on?: string
  payment_mode?: string
  description?: string
  attachment?: string
}
export interface WhatsAppTemplate extends BaseDoc {
  template_name: string
  purpose: string
  enabled: 0 | 1
  meta_template_name?: string
  language_code?: string
  body: string
}
export interface WhatsAppMessage extends BaseDoc {
  tenant?: string
  property?: string
  mobile: string
  template?: string
  status: 'Queued' | 'Sent' | 'Failed'
  sent_at?: string
  message?: string
  error?: string
  reference_doctype?: string
  reference_name?: string
}
export interface AppNotification {
  name: string
  subject: string
  document_type?: string
  document_name?: string
  read: 0 | 1
  creation: string
}
export interface Option {
  value: string
  label: string
  hint?: string
}
export interface NamedValue {
  name: string
  value: number
  count?: number
}
