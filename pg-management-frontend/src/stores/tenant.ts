import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tenantService, type TenantDetails } from '@/services/tenant.service'

/** Short-lived cache of tenant 360° views (invalidated on any tenant mutation). */
export const useTenantStore = defineStore('tenant', () => {
  const details = ref<Record<string, { at: number; data: TenantDetails }>>({})

  async function fetchDetails(name: string, force = false) {
    const hit = details.value[name]
    if (!force && hit && Date.now() - hit.at < 30_000) return hit.data
    const data = await tenantService.details(name)
    details.value[name] = { at: Date.now(), data }
    return data
  }
  function invalidate(name?: string) {
    if (name) delete details.value[name]
    else details.value = {}
  }
  return { details, fetchDetails, invalidate }
})
