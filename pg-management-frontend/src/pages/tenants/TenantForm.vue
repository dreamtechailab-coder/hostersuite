<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { NativeSelect } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Checkbox } from '@/components/ui/checkbox'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import FileUploader from '@/components/common/FileUploader.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { tenantService } from '@/services/tenant.service'
import { useMutation } from '@/composables/useMutation'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { useTenantStore } from '@/stores/tenant'
import { aadhaar, email, mobile, pan, required, validate, type Rule } from '@/utils/validation'
import type { Tenant } from '@/types'

const props = defineProps<{ name?: string }>()
const router = useRouter()
const { hasRole } = usePermissions()
const property = usePropertyStore()
const tenantStore = useTenantStore()
// Only admins/managers can record identity numbers (field-level permission on the server too)
const canKyc = hasRole('PG Admin', 'PG Manager')

const form = reactive<Partial<Tenant>>({
  full_name: '', mobile: '', email: '', gender: '', property: property.filter || '', date_of_birth: '', occupation: '', organization: '',
  permanent_address: '', id_type: 'Aadhaar', id_number: '', id_document: '', kyc_verified: 0, emergency_contact_name: '',
  emergency_contact_phone: '', whatsapp_opt_in: 1, notes: '', photo: '',
})
const masked = ref<string | null>(null)
const errors = ref<Record<string, string>>({})
const loading = ref(!!props.name)
const loadError = ref<Error | null>(null)

onMounted(async () => {
  if (!props.name) return
  try {
    const t = (await tenantService.get(props.name)).data
    Object.assign(form, { ...t, id_number: '' })
    masked.value = t.id_number_masked || null
  } catch (e) {
    loadError.value = e as Error
  } finally {
    loading.value = false
  }
})
const idRule: Rule = (v, f) => (f?.id_type === 'Aadhaar' ? aadhaar(v) : f?.id_type === 'PAN' ? pan(v) : true)
const save = useMutation(tenantService.save, { success: 'Tenant saved' })
async function submit() {
  errors.value = validate(form, {
    full_name: [required('Full name')], mobile: [required('Mobile'), mobile], email: [email], property: [required('Property')],
    id_number: [idRule], emergency_contact_phone: [mobile],
  })
  if (Object.keys(errors.value).length) return window.scrollTo({ top: 0, behavior: 'smooth' })
  const payload: Record<string, unknown> = { ...form }
  if (!payload.id_number) delete payload.id_number // keep existing (never sent back to the client)
  if (!canKyc) {
    delete payload.id_number
    delete payload.id_document
  }
  for (const k of ['id_number_masked', 'has_id_document', 'status', 'creation', 'modified', 'docstatus', 'owner', 'modified_by', 'idx']) delete payload[k]
  const res = await save.run(payload as Partial<Tenant>)
  if (res) {
    tenantStore.invalidate(res.data.name)
    router.replace(`/tenants/${res.data.name}`)
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader :title="name ? 'Edit tenant' : 'New tenant'" back />
    <ErrorState v-if="loadError" :error="loadError" />
    <LoadingSkeleton v-else-if="loading" variant="form" />
    <form v-else class="space-y-5" novalidate @submit.prevent="submit">
      <Card>
        <CardHeader><CardTitle>Personal details</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id, invalid }" label="Full name" required :error="errors.full_name" class="sm:col-span-2">
            <Input :id="id" v-model="form.full_name" autocomplete="name" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Mobile" required :error="errors.mobile">
            <Input :id="id" v-model="form.mobile" type="tel" inputmode="tel" autocomplete="tel" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Email" :error="errors.email">
            <Input :id="id" v-model="form.email" type="email" autocomplete="email" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id }" label="Gender"><NativeSelect :id="id" v-model="form.gender" :options="['Male', 'Female', 'Other']" placeholder="Select" /></FormField>
          <FormField v-slot="{ id }" label="Date of birth"><Input :id="id" v-model="form.date_of_birth" type="date" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property" class="sm:col-span-2">
            <SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id }" label="Occupation"><Input :id="id" v-model="form.occupation" /></FormField>
          <FormField v-slot="{ id }" label="Company / College"><Input :id="id" v-model="form.organization" /></FormField>
          <FormField v-slot="{ id }" label="Permanent address" class="sm:col-span-2"><Textarea :id="id" v-model="form.permanent_address" rows="2" /></FormField>
          <FormField label="Photo" class="sm:col-span-2">
            <FileUploader v-model="form.photo" accept="image/*" label="Upload photo" :doctype="name ? 'PG Tenant' : undefined" :docname="name" fieldname="photo" />
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle class="flex items-center gap-2"><ShieldCheck class="size-4 text-primary" />Identity (KYC)</CardTitle>
            <CardDescription>Stored privately. Only the last 4 digits are ever shown.</CardDescription>
          </div>
        </CardHeader>
        <CardContent v-if="canKyc" class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id }" label="ID type"><NativeSelect :id="id" v-model="form.id_type" :options="['Aadhaar', 'PAN', 'Passport', 'Driving License', 'Voter ID']" placeholder="Select" /></FormField>
          <FormField v-slot="{ id, invalid }" label="ID number" :error="errors.id_number" :hint="masked ? `On file: ${masked}. Leave blank to keep.` : undefined">
            <Input :id="id" v-model="form.id_number" autocomplete="off" :aria-invalid="invalid" :placeholder="masked ? 'Enter to replace' : ''" />
          </FormField>
          <FormField label="ID document" class="sm:col-span-2">
            <FileUploader v-model="form.id_document" :doctype="name ? 'PG Tenant' : undefined" :docname="name" fieldname="id_document" label="Upload ID proof" />
          </FormField>
          <label class="flex items-center gap-2 text-sm sm:col-span-2"><Checkbox :model-value="!!form.kyc_verified" @update:model-value="form.kyc_verified = $event ? 1 : 0" />KYC verified against original document</label>
        </CardContent>
        <CardContent v-else class="text-sm text-muted-foreground">Identity details can only be recorded by a manager or admin.</CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Emergency contact & preferences</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id }" label="Contact name"><Input :id="id" v-model="form.emergency_contact_name" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Contact phone" :error="errors.emergency_contact_phone"><Input :id="id" v-model="form.emergency_contact_phone" type="tel" :aria-invalid="invalid" /></FormField>
          <label class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium sm:col-span-2">
            Send WhatsApp updates (reminders, receipts)
            <Switch :model-value="!!form.whatsapp_opt_in" @update:model-value="form.whatsapp_opt_in = $event ? 1 : 0" />
          </label>
          <FormField v-slot="{ id }" label="Notes" class="sm:col-span-2"><Textarea :id="id" v-model="form.notes" rows="2" /></FormField>
        </CardContent>
      </Card>

      <div class="sticky bottom-20 flex justify-end gap-2 rounded-xl border bg-card/95 p-3 backdrop-blur lg:bottom-4">
        <Button variant="outline" @click="router.back()">Cancel</Button>
        <Button type="submit" :loading="save.pending.value">Save tenant</Button>
      </div>
    </form>
  </div>
</template>
