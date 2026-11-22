import { api } from './api'
import { resource } from './resource.service'
import type { WhatsAppMessage, WhatsAppTemplate } from '@/types'

export interface WhatsAppDashboard {
  enabled: boolean
  configured: boolean
  by_status: Record<string, number>
  daily: { day: string; sent: number; failed: number }[]
  templates: number
  opted_in_tenants: number
}

export const whatsappService = {
  dashboard: (property?: string) => api.pgGet<{ data: WhatsAppDashboard }>('whatsapp.get_dashboard', { property }).then((r) => r.data),
  templates: (params = {}) => resource.list<WhatsAppTemplate>('PG WhatsApp Template', params),
  saveTemplate: (data: Partial<WhatsAppTemplate>) => resource.save<WhatsAppTemplate>('PG WhatsApp Template', data),
  removeTemplate: (name: string) => resource.remove('PG WhatsApp Template', name),
  logs: (params = {}) => resource.list<WhatsAppMessage>('PG WhatsApp Message', params),
  send: (tenant: string, template?: string, message?: string) =>
    api.pgPost<{ message: string }>('whatsapp.send_message', { tenant, template, message }),
  bulkReminders: (property?: string) => api.pgPost<{ message: string }>('whatsapp.send_bulk_reminders', { property }),
  preview: (template: string, tenant?: string) =>
    api.pgPost<{ data: { text: string; placeholders: string[] } }>('whatsapp.preview_template', { template, tenant }).then((r) => r.data),
  retry: (name: string) => api.pgPost<{ message: string }>('whatsapp.retry_message', { name }),
}
