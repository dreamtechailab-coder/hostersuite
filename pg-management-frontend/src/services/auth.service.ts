import { api, setCsrfToken } from './api'
import type { SessionInfo } from '@/types'

export const authService = {
  async getSession(): Promise<SessionInfo> {
    const res = await api.pgGet<{ data: SessionInfo }>('session.get_session')
    setCsrfToken(res.data.csrf_token)
    return res.data
  },
  login: (usr: string, pwd: string) => api.post<{ message: string; full_name: string }>('login', { usr, pwd }),
  logout: () => api.post('logout'),
  forgotPassword: (user: string) => api.post('frappe.core.doctype.user.user.reset_password', { user }),
  resetPassword: (key: string, new_password: string) =>
    api.post<{ message?: string } | string>('frappe.core.doctype.user.user.update_password', {
      key,
      new_password,
      logout_all_sessions: 1,
    }),
  passwordStrength: (new_password: string) =>
    api.post<{ score: number; feedback?: { warning?: string; suggestions?: string[]; password_policy_validation_passed?: boolean } }>(
      'frappe.core.doctype.user.user.test_password_strength',
      { new_password },
    ),
}
