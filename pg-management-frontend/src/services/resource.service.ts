import { api } from './api'
import type { DataResponse, DocType, Filters, ListResponse, Option } from '@/types'

export interface ListParams {
  filters?: Filters
  search?: string
  page?: number
  page_size?: number
  order_by?: string
}

/** Generic, allow-listed CRUD (pg_managment_system.api.resource). */
export const resource = {
  list: <T>(doctype: DocType, params: ListParams = {}) =>
    api.pgGet<ListResponse<T>>('resource.get_list', { doctype, ...params }),
  get: <T>(doctype: DocType, name: string) => api.pgGet<DataResponse<T>>('resource.get_doc', { doctype, name }),
  save: <T>(doctype: DocType, data: Partial<T> & Record<string, unknown>) =>
    api.pgPost<DataResponse<T>>('resource.save_doc', { doctype, data }),
  remove: (doctype: DocType, name: string) => api.pgPost<DataResponse<{ name: string }>>('resource.delete_doc', { doctype, name }),
  submit: <T>(doctype: DocType, name: string) => api.pgPost<DataResponse<T>>('resource.submit_doc', { doctype, name }),
  cancel: <T>(doctype: DocType, name: string) => api.pgPost<DataResponse<T>>('resource.cancel_doc', { doctype, name }),
  options: (doctype: DocType, params: { filters?: Filters; search?: string; limit?: number } = {}) =>
    api.pgGet<{ data: Option[] }>('resource.get_options', { doctype, ...params }).then((r) => r.data),
}
