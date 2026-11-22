<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SettingsNav from './SettingsNav.vue'
import { settingsService } from '@/services/settings.service'
import { useMutation } from '@/composables/useMutation'
import { useAuthStore } from '@/stores/auth'
import { between, email, nonNegative, required, validate } from '@/utils/validation'

const auth = useAuthStore()
const form = reactive<Record<string, any>>({})
const errors = ref<Record<string, string>>({})
const loading = ref(true)
const error = ref<Error | null>(null)
onMounted(async () => {
  try {
    Object.assign(form, await settingsService.get())
  } catch (e) {
    error.value = e as Error
  } finally {
    loading.value = false
  }
})
const save = useMutation(settingsService.update)
async function submit() {
  errors.value = validate(form, {
    organization_name: [required('Organisation name')], support_email: [email], default_rent_due_day: [between(1, 28, 'Due day')],
    invoice_generation_day: [between(1, 28, 'Generation day')], late_fee_amount: [nonNegative('Late fee')],
  })
  if (Object.keys(errors.value).length) return
  const { whatsapp_access_token_set: _a, vapid_private_key_set: _b, ...data } = form
  if (await save.run(data)) auth.refresh()
}
const toggle = (k: string) => (v: boolean) => (form[k] = v ? 1 : 0)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader title="Settings" />
    <SettingsNav />
    <ErrorState v-if="error" :error="error" />
    <LoadingSkeleton v-else-if="loading" variant="form" />
    <form v-else class="space-y-5" novalidate @submit.prevent="submit">
      <Card>
        <CardHeader><CardTitle>Organisation</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id, invalid }" label="Organisation name" required :error="errors.organization_name" class="sm:col-span-2"><Input :id="id" v-model="form.organization_name" :aria-invalid="invalid" /></FormField>
          <FormField v-slot="{ id }" label="Currency" hint="ISO code, e.g. INR"><Input :id="id" v-model="form.currency" maxlength="3" class="uppercase" /></FormField>
          <FormField v-slot="{ id }" label="Support phone"><Input :id="id" v-model="form.support_phone" type="tel" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Support email" :error="errors.support_email" class="sm:col-span-2"><Input :id="id" v-model="form.support_email" type="email" :aria-invalid="invalid" /></FormField>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><div><CardTitle>Billing</CardTitle><CardDescription>Automatic invoicing runs daily in the background.</CardDescription></div></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id, invalid }" label="Default rent due day" :error="errors.default_rent_due_day"><Input :id="id" v-model.number="form.default_rent_due_day" type="number" min="1" max="28" :aria-invalid="invalid" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Invoice generation day" :error="errors.invoice_generation_day"><Input :id="id" v-model.number="form.invoice_generation_day" type="number" min="1" max="28" :aria-invalid="invalid" /></FormField>
          <label class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium sm:col-span-2">Auto-generate monthly invoices<Switch :model-value="!!form.auto_generate_invoices" @update:model-value="toggle('auto_generate_invoices')($event)" /></label>
          <FormField v-slot="{ id, invalid }" label="Late fee (once per overdue invoice)" :error="errors.late_fee_amount"><Input :id="id" v-model.number="form.late_fee_amount" type="number" min="0" :aria-invalid="invalid" /></FormField>
          <FormField v-slot="{ id }" label="Grace period (days)"><Input :id="id" v-model.number="form.late_fee_grace_days" type="number" min="0" /></FormField>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Reminders</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <label class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium sm:col-span-2">Send WhatsApp rent reminders automatically<Switch :model-value="!!form.send_rent_reminders" @update:model-value="toggle('send_rent_reminders')($event)" /></label>
          <FormField v-slot="{ id }" label="Days before due date"><Input :id="id" v-model.number="form.reminder_days_before_due" type="number" min="0" /></FormField>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><div><CardTitle>Web push</CardTitle><CardDescription>Optional. Requires the <code>pywebpush</code> package on the server.</CardDescription></div></CardHeader>
        <CardContent class="grid gap-4">
          <FormField v-slot="{ id }" label="VAPID public key"><Input :id="id" v-model="form.vapid_public_key" /></FormField>
          <FormField v-slot="{ id }" label="VAPID private key" :hint="form.vapid_private_key_set ? 'A key is saved. Enter a new one to replace it.' : 'Stored encrypted; never shown again.'"><Input :id="id" v-model="form.vapid_private_key" type="password" autocomplete="off" /></FormField>
          <FormField v-slot="{ id }" label="Contact (mailto:)"><Input :id="id" v-model="form.vapid_subject" placeholder="mailto:admin@example.com" /></FormField>
        </CardContent>
      </Card>
      <div class="sticky bottom-20 flex justify-end rounded-xl border bg-card/95 p-3 backdrop-blur lg:bottom-4"><Button type="submit" :loading="save.pending.value">Save settings</Button></div>
    </form>
  </div>
</template>
