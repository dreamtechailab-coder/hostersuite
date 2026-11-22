import { api } from './api'
import type { AppNotification, PgRole } from '@/types'

export interface PgUser {
  name: string
  full_name: string
  email: string
  enabled: 0 | 1
  last_login?: string
  mobile_no?: string
  user_image?: string
  roles: PgRole[]
  properties: string[]
}

export const settingsService = {
  get: () => api.pgGet<{ data: Record<string, any> }>('settings.get_settings').then((r) => r.data),
  update: (data: Record<string, unknown>) => api.pgPost<{ data: Record<string, any>; message: string }>('settings.update_settings', { data }),
  users: (params: { search?: string; page?: number; page_size?: number }) =>
    api.pgGet<{ data: PgUser[]; total: number; page: number; page_size: number }>('users.list_users', params),
  saveUser: (data: Record<string, unknown>) => api.pgPost<{ message: string }>('users.save_user', { data }),
  roleMatrix: () =>
    api
      .pgGet<{ data: { roles: PgRole[]; doctypes: string[]; matrix: Record<string, Record<string, Record<string, boolean>>>; user_counts: Record<string, number> } }>(
        'users.get_role_matrix',
      )
      .then((r) => r.data),
}

export const notificationService = {
  list: () => api.pgGet<{ data: AppNotification[]; unread: number }>('notifications.get_notifications'),
  markRead: (name?: string) => api.pgPost('notifications.mark_read', { name }),
  savePush: (subscription: PushSubscriptionJSON) =>
    api.pgPost('notifications.save_push_subscription', { subscription, user_agent: navigator.userAgent }),
  removePush: (endpoint: string) => api.pgPost('notifications.remove_push_subscription', { endpoint }),
}

export const searchService = {
  search: (q: string) =>
    api
      .pgGet<{ data: { type: string; name: string; title: string; subtitle?: string }[] }>('search.global_search', { q })
      .then((r) => r.data),
}
