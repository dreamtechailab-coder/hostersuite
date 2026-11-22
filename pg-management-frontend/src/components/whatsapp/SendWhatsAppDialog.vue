<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { NativeSelect } from '@/components/ui/select'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import { whatsappService } from '@/services/whatsapp.service'
import { resource } from '@/services/resource.service'
import { useMutation } from '@/composables/useMutation'
import type { Option } from '@/types'

const props = defineProps<{ tenant: string; tenantName?: string }>()
const open = defineModel<boolean>('open', { default: false })
const templates = ref<Option[]>([])
const template = ref('')
const message = ref('')
const preview = ref('')
watch(open, async (o) => {
  if (!o) return
  template.value = ''
  message.value = ''
  preview.value = ''
  templates.value = await resource.options('PG WhatsApp Template', { filters: { enabled: 1 }, limit: 50 })
})
watch(template, async (t) => {
  preview.value = t ? (await whatsappService.preview(t, props.tenant)).text : ''
})
const send = useMutation(() => whatsappService.send(props.tenant, template.value || undefined, template.value ? undefined : message.value))
async function submit() {
  if (await send.run()) open.value = false
}
</script>

<template>
  <ModalDialog v-model:open="open" title="Send WhatsApp message" :description="tenantName">
    <div class="space-y-4">
      <FormField v-slot="{ id }" label="Template">
        <NativeSelect :id="id" v-model="template" :options="templates" placeholder="Custom message" />
      </FormField>
      <div v-if="template" class="rounded-lg bg-muted/60 p-3 text-sm whitespace-pre-line">{{ preview || 'Loading preview…' }}</div>
      <FormField v-else v-slot="{ id }" label="Message" hint="Free-text messages are only delivered within 24h of the tenant's last message (WhatsApp policy).">
        <Textarea :id="id" v-model="message" rows="4" />
      </FormField>
    </div>
    <template #footer>
      <Button variant="outline" @click="open = false">Cancel</Button>
      <Button :disabled="!template && !message.trim()" :loading="send.pending.value" @click="submit">Send</Button>
    </template>
  </ModalDialog>
</template>
