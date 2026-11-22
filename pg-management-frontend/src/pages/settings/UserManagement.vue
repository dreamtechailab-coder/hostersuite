<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { Plus, Pencil } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'
import { Avatar } from '@/components/ui/avatar'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchInput from '@/components/common/SearchInput.vue'
import DataTable from '@/components/common/DataTable.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import SettingsNav from './SettingsNav.vue'
import { settingsService, type PgUser } from '@/services/settings.service'
import { resource } from '@/services/resource.service'
import { useAsync } from '@/composables/useAsync'
import { useMutation } from '@/composables/useMutation'
import { usePagination } from '@/composables/usePagination'
import { email, required, validate } from '@/utils/validation'
import { relativeTime } from '@/utils/date'
import type { Option, PgRole } from '@/types'

const ROLES: { role: PgRole; text: string }[] = [
  { role: 'PG Admin', text: 'Everything, including settings and users' },
  { role: 'PG Manager', text: 'Day-to-day operations for assigned properties' },
  { role: 'PG Accountant', text: 'Invoices, payments, expenses and reports' },
  { role: 'PG Staff', text: 'Front desk: tenants, bookings, meter readings' },
]
const search = ref('')
const pg = usePagination(20)
const { data, loading, error, run } = useAsync(async () => {
  const res = await settingsService.users({ search: search.value || undefined, page: pg.page.value, page_size: pg.pageSize.value })
  pg.total.value = res.total
  return res.data
}, { immediate: true })
watch(pg.page, () => run())
watchDebounced(search, () => (pg.page.value = 1, run()), { debounce: 300 })
const properties = ref<Option[]>([])
resource.options('PG Property', { limit: 200 }).then((r) => (properties.value = r))

const open = ref(false)
const isNew = ref(true)
const form = reactive({ email: '', first_name: '', last_name: '', mobile_no: '', roles: [] as PgRole[], properties: [] as string[], enabled: 1, send_welcome_email: 1 })
const errors = ref<Record<string, string>>({})
function edit(u?: PgUser) {
  isNew.value = !u
  errors.value = {}
  const [first, ...rest] = (u?.full_name || '').split(' ')
  Object.assign(form, { email: u?.email || '', first_name: first || '', last_name: rest.join(' '), mobile_no: u?.mobile_no || '', roles: [...(u?.roles || ['PG Staff'])], properties: [...(u?.properties || [])], enabled: u ? u.enabled : 1, send_welcome_email: 1 })
  open.value = true
}
function toggle<T>(arr: T[], v: T, on: boolean) {
  const i = arr.indexOf(v)
  if (on && i < 0) arr.push(v)
  if (!on && i >= 0) arr.splice(i, 1)
}
const save = useMutation(settingsService.saveUser)
async function submit() {
  errors.value = validate(form, { email: [required('Email'), email], first_name: [required('First name')] })
  if (!form.roles.length) errors.value.roles = 'Pick at least one role'
  if (!form.roles.includes('PG Admin') && !form.properties.length) errors.value.properties = 'Non-admin users need at least one property'
  if (Object.keys(errors.value).length) return
  if (await save.run({ ...form })) {
    open.value = false
    run()
  }
}
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <PageHeader title="Settings">
      <template #actions><Button @click="edit()"><Plus />Invite user</Button></template>
    </PageHeader>
    <SettingsNav />
    <div class="mb-4"><SearchInput v-model="search" placeholder="Search users…" /></div>
    <DataTable
      :columns="[
        { key: 'full_name', label: 'User' },
        { key: 'roles', label: 'Roles' },
        { key: 'properties', label: 'Properties' },
        { key: 'last_login', label: 'Last login', mobileHidden: true },
        { key: 'enabled', label: 'Status' },
      ]"
      :rows="data || []"
      :loading="loading"
      :error="error"
      clickable
      :pagination="{ page: pg.page.value, pageCount: pg.pageCount.value, total: pg.total.value, from: pg.from.value, to: pg.to.value }"
      @update:page="pg.setPage"
      @row-click="edit"
      @retry="run"
    >
      <template #cell-full_name="{ row }">
        <span class="flex items-center gap-3"><Avatar :name="row.full_name" :src="row.user_image" class="size-8" /><span class="min-w-0"><span class="block truncate font-medium">{{ row.full_name }}</span><span class="block truncate text-xs text-muted-foreground">{{ row.email }}</span></span></span>
      </template>
      <template #cell-roles="{ value }"><span class="flex flex-wrap gap-1"><Badge v-for="r in value" :key="r" variant="secondary">{{ r.replace('PG ', '') }}</Badge></span></template>
      <template #cell-properties="{ row }">{{ row.roles.includes('PG Admin') ? 'All' : row.properties.length ? row.properties.join(', ') : 'None' }}</template>
      <template #cell-last_login="{ value }">{{ value ? relativeTime(value) : 'Never' }}</template>
      <template #cell-enabled="{ value }"><Badge :variant="value ? 'success' : 'neutral'">{{ value ? 'Active' : 'Disabled' }}</Badge></template>
      <template #row-actions="{ row }"><Button variant="ghost" size="icon-sm" :aria-label="`Edit ${row.full_name}`" @click="edit(row)"><Pencil /></Button></template>
    </DataTable>

    <ModalDialog v-model:open="open" :title="isNew ? 'Invite user' : 'Edit user'" :description="isNew ? 'They will receive an email to set their password.' : form.email" size="lg">
      <form id="user-form" class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
        <FormField v-slot="{ id, invalid }" label="Email" required :error="errors.email" class="sm:col-span-2"><Input :id="id" v-model="form.email" type="email" :disabled="!isNew" :aria-invalid="invalid" /></FormField>
        <FormField v-slot="{ id, invalid }" label="First name" required :error="errors.first_name"><Input :id="id" v-model="form.first_name" :aria-invalid="invalid" /></FormField>
        <FormField v-slot="{ id }" label="Last name"><Input :id="id" v-model="form.last_name" /></FormField>
        <FormField v-slot="{ id }" label="Mobile"><Input :id="id" v-model="form.mobile_no" type="tel" /></FormField>
        <label class="flex items-center justify-between gap-3 self-end rounded-lg border px-3 py-2.5 text-sm font-medium">Active<Switch :model-value="!!form.enabled" @update:model-value="form.enabled = $event ? 1 : 0" /></label>
        <fieldset class="sm:col-span-2">
          <legend class="mb-2 text-[13px] font-medium">Roles</legend>
          <div class="grid gap-2 sm:grid-cols-2">
            <label v-for="r in ROLES" :key="r.role" class="flex cursor-pointer gap-3 rounded-lg border p-3 has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5">
              <Checkbox :model-value="form.roles.includes(r.role)" @update:model-value="toggle(form.roles, r.role, !!$event)" />
              <span><span class="block text-sm font-medium">{{ r.role.replace('PG ', '') }}</span><span class="block text-xs text-muted-foreground">{{ r.text }}</span></span>
            </label>
          </div>
          <p v-if="errors.roles" class="mt-1 text-xs font-medium text-destructive">{{ errors.roles }}</p>
        </fieldset>
        <fieldset v-if="!form.roles.includes('PG Admin')" class="sm:col-span-2">
          <legend class="mb-2 text-[13px] font-medium">Property access</legend>
          <div class="grid max-h-48 gap-1.5 overflow-y-auto rounded-lg border p-2 sm:grid-cols-2">
            <label v-for="p in properties" :key="p.value" class="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted">
              <Checkbox :model-value="form.properties.includes(p.value)" @update:model-value="toggle(form.properties, p.value, !!$event)" />{{ p.label }}
            </label>
          </div>
          <p v-if="errors.properties" class="mt-1 text-xs font-medium text-destructive">{{ errors.properties }}</p>
        </fieldset>
        <p v-else class="rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground sm:col-span-2">Admins can access every property.</p>
      </form>
      <template #footer>
        <Button variant="outline" @click="open = false">Cancel</Button>
        <Button type="submit" form="user-form" :loading="save.pending.value">{{ isNew ? 'Send invite' : 'Save' }}</Button>
      </template>
    </ModalDialog>
  </div>
</template>
