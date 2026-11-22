import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { onSessionExpired } from '@/services/api'
import type { DocType, PermType, PgRole } from '@/types'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    guest?: boolean
    public?: boolean
    perm?: [DocType, PermType]
    roles?: PgRole[]
  }
}

const P = (doctype: DocType, perm: PermType = 'read'): [DocType, PermType] => [doctype, perm]

const appRoutes: RouteRecordRaw[] = [
  { path: '', name: 'dashboard', component: () => import('@/pages/dashboard/Dashboard.vue'), meta: { title: 'Dashboard' } },

  { path: 'properties', name: 'properties', component: () => import('@/pages/properties/PropertyList.vue'), meta: { title: 'Properties', perm: P('PG Property') } },
  { path: 'properties/new', name: 'property-new', component: () => import('@/pages/properties/PropertyForm.vue'), meta: { title: 'New property', roles: ['PG Admin'] } },
  { path: 'properties/:name', name: 'property', component: () => import('@/pages/properties/PropertyDetails.vue'), props: true, meta: { title: 'Property', perm: P('PG Property') } },
  { path: 'properties/:name/edit', name: 'property-edit', component: () => import('@/pages/properties/PropertyForm.vue'), props: true, meta: { title: 'Edit property', perm: P('PG Property', 'write') } },

  { path: 'buildings', name: 'buildings', component: () => import('@/pages/buildings/BuildingList.vue'), meta: { title: 'Buildings', perm: P('PG Building') } },
  { path: 'buildings/:name', name: 'building', component: () => import('@/pages/buildings/BuildingDetails.vue'), props: true, meta: { title: 'Building', perm: P('PG Building') } },
  { path: 'floors', name: 'floors', component: () => import('@/pages/floors/FloorList.vue'), meta: { title: 'Floors', perm: P('PG Floor') } },

  { path: 'rooms', name: 'rooms', component: () => import('@/pages/rooms/RoomList.vue'), meta: { title: 'Rooms', perm: P('PG Room') } },
  { path: 'rooms/allocate', name: 'bed-allocation', component: () => import('@/pages/rooms/BedAllocation.vue'), meta: { title: 'Bed allocation', perm: P('PG Occupancy', 'create') } },
  { path: 'rooms/:name', name: 'room', component: () => import('@/pages/rooms/RoomDetails.vue'), props: true, meta: { title: 'Room', perm: P('PG Room') } },

  { path: 'tenants', name: 'tenants', component: () => import('@/pages/tenants/TenantList.vue'), meta: { title: 'Tenants', perm: P('PG Tenant') } },
  { path: 'tenants/new', name: 'tenant-new', component: () => import('@/pages/tenants/TenantForm.vue'), meta: { title: 'New tenant', perm: P('PG Tenant', 'create') } },
  { path: 'tenants/:name', name: 'tenant', component: () => import('@/pages/tenants/TenantDetails.vue'), props: true, meta: { title: 'Tenant', perm: P('PG Tenant') } },
  { path: 'tenants/:name/edit', name: 'tenant-edit', component: () => import('@/pages/tenants/TenantForm.vue'), props: true, meta: { title: 'Edit tenant', perm: P('PG Tenant', 'write') } },

  { path: 'bookings', name: 'bookings', component: () => import('@/pages/bookings/BookingList.vue'), meta: { title: 'Bookings', perm: P('PG Booking') } },
  { path: 'bookings/new', name: 'booking-new', component: () => import('@/pages/bookings/BookingForm.vue'), meta: { title: 'New booking', perm: P('PG Booking', 'create') } },
  { path: 'occupancy', name: 'occupancy', component: () => import('@/pages/occupancy/OccupancyList.vue'), meta: { title: 'Occupancy', perm: P('PG Occupancy') } },

  { path: 'rent', name: 'rent', component: () => import('@/pages/rent/RentDashboard.vue'), meta: { title: 'Rent', perm: P('PG Rent Invoice') } },
  { path: 'rent/invoices', name: 'invoices', component: () => import('@/pages/rent/RentInvoices.vue'), meta: { title: 'Invoices', perm: P('PG Rent Invoice') } },
  { path: 'rent/invoices/:name', name: 'invoice', component: () => import('@/pages/rent/InvoiceDetails.vue'), props: true, meta: { title: 'Invoice', perm: P('PG Rent Invoice') } },

  { path: 'electricity', name: 'electricity', component: () => import('@/pages/electricity/ElectricityDashboard.vue'), meta: { title: 'Electricity', perm: P('PG Meter Reading') } },
  { path: 'electricity/readings', name: 'meter-readings', component: () => import('@/pages/electricity/MeterReadings.vue'), meta: { title: 'Meter readings', perm: P('PG Meter Reading') } },
  { path: 'electricity/bills', name: 'electricity-bills', component: () => import('@/pages/electricity/ElectricityBills.vue'), meta: { title: 'Electricity bills', perm: P('PG Meter Reading') } },

  { path: 'payments', name: 'payments', component: () => import('@/pages/payments/PaymentList.vue'), meta: { title: 'Payments', perm: P('PG Payment') } },
  { path: 'payments/collect', name: 'payment-collect', component: () => import('@/pages/payments/PaymentCollection.vue'), meta: { title: 'Collect payment', perm: P('PG Payment', 'create') } },
  { path: 'payments/:name', name: 'payment', component: () => import('@/pages/payments/PaymentDetails.vue'), props: true, meta: { title: 'Payment', perm: P('PG Payment') } },

  { path: 'expenses', name: 'expenses', component: () => import('@/pages/expenses/ExpenseList.vue'), meta: { title: 'Expenses', perm: P('PG Expense') } },
  { path: 'expenses/new', name: 'expense-new', component: () => import('@/pages/expenses/ExpenseForm.vue'), meta: { title: 'New expense', perm: P('PG Expense', 'create') } },
  { path: 'expenses/:name/edit', name: 'expense-edit', component: () => import('@/pages/expenses/ExpenseForm.vue'), props: true, meta: { title: 'Edit expense', perm: P('PG Expense', 'write') } },

  { path: 'finance/receivables', name: 'receivables', component: () => import('@/pages/finance/Receivables.vue'), meta: { title: 'Receivables', perm: P('PG Rent Invoice') } },
  { path: 'finance/payables', name: 'payables', component: () => import('@/pages/finance/Payables.vue'), meta: { title: 'Payables', perm: P('PG Expense') } },
  { path: 'finance/reports', name: 'financial-reports', component: () => import('@/pages/finance/FinancialReports.vue'), meta: { title: 'Financial reports', perm: P('PG Expense') } },

  { path: 'whatsapp', name: 'whatsapp', component: () => import('@/pages/whatsapp/WhatsAppDashboard.vue'), meta: { title: 'WhatsApp', perm: P('PG WhatsApp Message') } },
  { path: 'whatsapp/templates', name: 'whatsapp-templates', component: () => import('@/pages/whatsapp/WhatsAppTemplates.vue'), meta: { title: 'WhatsApp templates', perm: P('PG WhatsApp Template') } },
  { path: 'whatsapp/logs', name: 'whatsapp-logs', component: () => import('@/pages/whatsapp/MessageLogs.vue'), meta: { title: 'Message logs', perm: P('PG WhatsApp Message') } },

  { path: 'reports/occupancy', name: 'report-occupancy', component: () => import('@/pages/reports/OccupancyReport.vue'), meta: { title: 'Occupancy report', perm: P('PG Occupancy') } },
  { path: 'reports/revenue', name: 'report-revenue', component: () => import('@/pages/reports/RevenueReport.vue'), meta: { title: 'Revenue report', perm: P('PG Rent Invoice') } },
  { path: 'reports/expenses', name: 'report-expenses', component: () => import('@/pages/reports/ExpenseReport.vue'), meta: { title: 'Expense report', perm: P('PG Expense') } },

  { path: 'settings', redirect: '/settings/general' },
  { path: 'settings/general', name: 'settings', component: () => import('@/pages/settings/GeneralSettings.vue'), meta: { title: 'Settings', roles: ['PG Admin'] } },
  { path: 'settings/users', name: 'users', component: () => import('@/pages/settings/UserManagement.vue'), meta: { title: 'Users', roles: ['PG Admin'] } },
  { path: 'settings/roles', name: 'roles', component: () => import('@/pages/settings/RoleManagement.vue'), meta: { title: 'Roles', roles: ['PG Admin'] } },
  { path: 'settings/whatsapp', name: 'whatsapp-settings', component: () => import('@/pages/settings/WhatsAppSettings.vue'), meta: { title: 'WhatsApp settings', roles: ['PG Admin'] } },

  { path: 'forbidden', name: 'forbidden', component: () => import('@/pages/Forbidden.vue'), meta: { title: 'No access' } },
]

const routes: RouteRecordRaw[] = [
  // Must come BEFORE the auth layout: both parents sit at '/', and vue-router
  // resolves '/' to whichever was registered first. If the auth layout wins,
  // '/' renders an empty AuthLayout and post-login navigation appears stuck.
  { path: '/', component: () => import('@/layouts/DashboardLayout.vue'), children: appRoutes },
  {
    path: '/',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      { path: 'login', name: 'login', component: () => import('@/pages/auth/Login.vue'), meta: { guest: true, title: 'Sign in' } },
      { path: 'forgot-password', name: 'forgot-password', component: () => import('@/pages/auth/ForgotPassword.vue'), meta: { guest: true, title: 'Forgot password' } },
      // Frappe's reset e-mails link to /update-password?key=… – served by this SPA via the reverse proxy
      { path: 'update-password', alias: '/reset-password', name: 'reset-password', component: () => import('@/pages/auth/ResetPassword.vue'), meta: { public: true, title: 'Set password' } },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFound.vue'), meta: { public: true, title: 'Not found' } },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: (_to, _from, saved) => saved || { top: 0 },
})

/**
 * Route guards are a USABILITY layer only. Every API call is authorised by the
 * backend regardless of what the router allows.
 */
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.init()
  if (to.meta.public) return true
  if (to.meta.guest) return auth.isLoggedIn ? { name: 'dashboard' } : true
  if (!auth.isLoggedIn) return { name: 'login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : undefined }
  if (to.meta.perm && !auth.can(to.meta.perm[0], to.meta.perm[1])) return { name: 'forbidden' }
  if (to.meta.roles && !auth.hasRole(...to.meta.roles)) return { name: 'forbidden' }
  return true
})

router.afterEach((to) => {
  const org = useAuthStore().settings?.organization_name
  document.title = [to.meta.title, org || 'HostelSuite'].filter(Boolean).join(' · ')
})

// lazy chunk failed after a deploy → hard reload to fetch the new build
router.onError((err, to) => {
  if (/Failed to fetch dynamically imported module|Importing a module script failed/i.test(String(err?.message))) {
    window.location.assign(router.resolve(to.fullPath).href)
  }
})

onSessionExpired(() => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn) return
  auth.clearSession()
  const current = router.currentRoute.value
  if (!current.meta.guest && !current.meta.public) router.replace({ name: 'login', query: { redirect: current.fullPath, expired: '1' } })
})

export default router
