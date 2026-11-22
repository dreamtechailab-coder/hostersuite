import type { Component } from 'vue'
import {
  BarChart3, BedDouble, Building, Building2, CalendarCheck, CreditCard, DoorOpen, FileText, Gauge, Landmark, Layers,
  LayoutDashboard, MessageCircle, PieChart, Receipt, Settings, Shield, UserCheck, Users, Wallet, Zap, HandCoins, TrendingUp,
} from 'lucide-vue-next'
import type { DocType, PermType, PgRole } from '@/types'

export interface NavItem {
  label: string
  to: string
  icon: Component
  perm?: [DocType, PermType]
  roles?: PgRole[]
  exact?: boolean
}
export interface NavGroup {
  label: string
  items: NavItem[]
}

export const NAV: NavGroup[] = [
  { label: 'Overview', items: [{ label: 'Dashboard', to: '/', icon: LayoutDashboard, exact: true }] },
  {
    label: 'Property',
    items: [
      { label: 'Properties', to: '/properties', icon: Building2, perm: ['PG Property', 'read'] },
      { label: 'Buildings', to: '/buildings', icon: Building, perm: ['PG Building', 'read'] },
      { label: 'Floors', to: '/floors', icon: Layers, perm: ['PG Floor', 'read'] },
      { label: 'Rooms', to: '/rooms', icon: DoorOpen, perm: ['PG Room', 'read'], exact: true },
      { label: 'Bed allocation', to: '/rooms/allocate', icon: BedDouble, perm: ['PG Occupancy', 'create'] },
    ],
  },
  {
    label: 'Residents',
    items: [
      { label: 'Tenants', to: '/tenants', icon: Users, perm: ['PG Tenant', 'read'] },
      { label: 'Bookings', to: '/bookings', icon: CalendarCheck, perm: ['PG Booking', 'read'] },
      { label: 'Occupancy', to: '/occupancy', icon: UserCheck, perm: ['PG Occupancy', 'read'] },
    ],
  },
  {
    label: 'Billing',
    items: [
      { label: 'Rent', to: '/rent', icon: Receipt, perm: ['PG Rent Invoice', 'read'], exact: true },
      { label: 'Invoices', to: '/rent/invoices', icon: FileText, perm: ['PG Rent Invoice', 'read'] },
      { label: 'Electricity', to: '/electricity', icon: Zap, perm: ['PG Meter Reading', 'read'] },
      { label: 'Payments', to: '/payments', icon: CreditCard, perm: ['PG Payment', 'read'] },
      { label: 'Expenses', to: '/expenses', icon: Wallet, perm: ['PG Expense', 'read'] },
    ],
  },
  {
    label: 'Finance',
    items: [
      { label: 'Receivables', to: '/finance/receivables', icon: HandCoins, perm: ['PG Rent Invoice', 'read'] },
      { label: 'Payables', to: '/finance/payables', icon: Landmark, perm: ['PG Expense', 'read'] },
      { label: 'Financial reports', to: '/finance/reports', icon: TrendingUp, perm: ['PG Expense', 'read'] },
    ],
  },
  {
    label: 'Engage & analyse',
    items: [
      { label: 'WhatsApp', to: '/whatsapp', icon: MessageCircle, perm: ['PG WhatsApp Message', 'read'] },
      { label: 'Occupancy report', to: '/reports/occupancy', icon: Gauge, perm: ['PG Occupancy', 'read'] },
      { label: 'Revenue report', to: '/reports/revenue', icon: BarChart3, perm: ['PG Rent Invoice', 'read'] },
      { label: 'Expense report', to: '/reports/expenses', icon: PieChart, perm: ['PG Expense', 'read'] },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Settings', to: '/settings/general', icon: Settings, roles: ['PG Admin'] },
      { label: 'Users', to: '/settings/users', icon: Users, roles: ['PG Admin'] },
      { label: 'Roles', to: '/settings/roles', icon: Shield, roles: ['PG Admin'] },
    ],
  },
]
