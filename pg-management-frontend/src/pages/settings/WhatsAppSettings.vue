<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ExternalLink, ShieldCheck } from 'lucide-vue-next'
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

const auth = useAuthStore()
const form = reactive({ whatsapp_enabled: 0, whatsapp_api_base: '', whatsapp_api_version: '', whatsapp_phone_number_id: '', whatsapp_default_country_code: '', whatsapp_access_token: '' })
const tokenSet = ref(false)
const loading = ref(true)
const error = ref<Error | null>(null)
onMounted(async () => {
  try {
    const s = await settingsService.get()
    for (const k of Object.keys(form) as (keyof typeof form)[]) if (k !== 'whatsapp_access_token') (form as any)[k] = s[k] ?? ''
    tokenSet.value = !!s.whatsapp_access_token_set
  } catch (e) {
    error.value = e as Error
  } finally {
    loading.value = false
  }
})
const save = useMutation(settingsService.update)
async function submit() {
  const res = await save.run({ ...form })
  if (res) {
    tokenSet.value = !!res.data.whatsapp_access_token_set
    form.whatsapp_access_token = ''
    auth.refresh()
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader title="Settings" />
    <SettingsNav />
    <ErrorState v-if="error" :error="error" />
    <LoadingSkeleton v-else-if="loading" variant="form" />
    <form v-else class="space-y-5" @submit.prevent="submit">
      <Card>
        <CardHeader>
          <div><CardTitle>WhatsApp Cloud API</CardTitle><CardDescription>Messages are sent from the server – your access token never reaches the browser.</CardDescription></div>
          <a href="https://developers.facebook.com/docs/whatsapp/cloud-api/get-started" target="_blank" rel="noopener" class="inline-flex items-center gap-1 text-sm text-primary hover:underline">Setup guide<ExternalLink class="size-3.5" /></a>
        </CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <label class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium sm:col-span-2">Enable WhatsApp messaging<Switch :model-value="!!form.whatsapp_enabled" @update:model-value="form.whatsapp_enabled = $event ? 1 : 0" /></label>
          <FormField v-slot="{ id }" label="Phone number ID"><Input :id="id" v-model="form.whatsapp_phone_number_id" /></FormField>
          <FormField v-slot="{ id }" label="Default country code"><Input :id="id" v-model="form.whatsapp_default_country_code" inputmode="numeric" /></FormField>
          <FormField v-slot="{ id }" label="Permanent access token" class="sm:col-span-2" :hint="tokenSet ? 'A token is saved (encrypted). Enter a new one only to replace it.' : 'Stored encrypted on the server.'">
            <Input :id="id" v-model="form.whatsapp_access_token" type="password" autocomplete="off" :placeholder="tokenSet ? '••••••••••••' : ''" />
          </FormField>
          <FormField v-slot="{ id }" label="API base URL"><Input :id="id" v-model="form.whatsapp_api_base" /></FormField>
          <FormField v-slot="{ id }" label="API version"><Input :id="id" v-model="form.whatsapp_api_version" /></FormField>
          <p class="flex items-center gap-2 text-xs text-muted-foreground sm:col-span-2"><ShieldCheck class="size-4 text-success" />Business-initiated messages (reminders) require approved templates – set their names under WhatsApp → Templates.</p>
        </CardContent>
      </Card>
      <div class="flex justify-end"><Button type="submit" :loading="save.pending.value">Save</Button></div>
    </form>
  </div>
</template>
