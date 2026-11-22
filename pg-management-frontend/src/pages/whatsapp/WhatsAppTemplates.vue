<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Plus, Pencil, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { NativeSelect } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Card, CardContent } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'
import FormField from '@/components/common/FormField.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { whatsappService } from '@/services/whatsapp.service'
import { useResourceList } from '@/composables/useResourceList'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { required, validate } from '@/utils/validation'
import type { WhatsAppTemplate } from '@/types'

const PURPOSES = ['Rent Reminder', 'Invoice Issued', 'Payment Receipt', 'Welcome', 'Booking Confirmation', 'General']
const VARS = ['tenant_name', 'amount', 'total', 'due_date', 'period', 'invoice', 'payment', 'date', 'property', 'room', 'check_in', 'booking', 'organization']
const { can } = usePermissions()
const { confirm } = useConfirm()
const list = useResourceList<WhatsAppTemplate>('PG WhatsApp Template', { scoped: false, pageSize: 50 })
const open = ref(false)
const isNew = ref(true)
const form = reactive<Partial<WhatsAppTemplate>>({})
const errors = ref<Record<string, string>>({})
function edit(t?: WhatsAppTemplate) {
  isNew.value = !t
  errors.value = {}
  Object.assign(form, t ? { ...t } : { name: undefined, template_name: '', purpose: 'General', enabled: 1, meta_template_name: '', language_code: 'en', body: '' })
  open.value = true
}
function insertVar(v: string) {
  form.body = `${form.body || ''}{{${v}}}`
}
const preview = computed(() => (form.body || '').replace(/{{\s*(\w+)\s*}}/g, (_m, k) => `[${k}]`))
const save = useMutation(whatsappService.saveTemplate, { success: 'Template saved' })
const del = useMutation(whatsappService.removeTemplate, { success: 'Template deleted' })
async function submit() {
  errors.value = validate(form, { template_name: [required('Name')], body: [required('Message')] })
  if (Object.keys(errors.value).length) return
  if (await save.run(form)) {
    open.value = false
    list.reload()
  }
}
async function remove(t: WhatsAppTemplate) {
  const { confirmed } = await confirm({ title: `Delete “${t.template_name}”?`, destructive: true, confirmText: 'Delete' })
  if (confirmed && (await del.run(t.name))) list.reload()
}
</script>

<template>
  <div>
    <PageHeader title="WhatsApp templates" description="Messages sent automatically for reminders, receipts and more." back="/whatsapp">
      <template #actions><Button v-if="can('PG WhatsApp Template', 'create')" @click="edit()"><Plus />New template</Button></template>
    </PageHeader>
    <ErrorState v-if="list.error.value" :error="list.error.value" @retry="list.reload" />
    <LoadingSkeleton v-else-if="list.loading.value && !list.rows.value.length" variant="cards" />
    <EmptyState v-else-if="!list.rows.value.length" title="No templates" />
    <div v-else class="grid gap-3 md:grid-cols-2">
      <Card v-for="t in list.rows.value" :key="t.name">
        <CardContent>
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="font-semibold">{{ t.template_name }}</p>
              <p class="text-xs text-muted-foreground">{{ t.purpose }}<template v-if="t.meta_template_name"> · Meta: {{ t.meta_template_name }}</template></p>
            </div>
            <StatusBadge :status="t.enabled ? 'Enabled' : 'Disabled'" />
          </div>
          <p class="mt-3 line-clamp-3 rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">{{ t.body }}</p>
          <div v-if="can('PG WhatsApp Template', 'write')" class="mt-3 flex justify-end gap-1">
            <Button size="sm" variant="ghost" @click="edit(t)"><Pencil />Edit</Button>
            <Button v-if="can('PG WhatsApp Template', 'delete')" size="sm" variant="ghost" @click="remove(t)"><Trash2 />Delete</Button>
          </div>
        </CardContent>
      </Card>
    </div>
    <ModalDialog v-model:open="open" :title="isNew ? 'New template' : 'Edit template'" size="lg">
      <form id="tpl-form" class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
        <FormField v-slot="{ id, invalid }" label="Name" required :error="errors.template_name"><Input :id="id" v-model="form.template_name" :disabled="!isNew" :aria-invalid="invalid" /></FormField>
        <FormField v-slot="{ id }" label="Used for"><NativeSelect :id="id" v-model="form.purpose" :options="PURPOSES" /></FormField>
        <FormField v-slot="{ id }" label="Approved Meta template name" hint="Required for business-initiated messages"><Input :id="id" v-model="form.meta_template_name" /></FormField>
        <FormField v-slot="{ id }" label="Language code"><Input :id="id" v-model="form.language_code" /></FormField>
        <FormField v-slot="{ id, invalid }" label="Message" required :error="errors.body" class="sm:col-span-2">
          <Textarea :id="id" v-model="form.body" rows="5" :aria-invalid="invalid" />
        </FormField>
        <div class="sm:col-span-2">
          <p class="mb-1.5 text-xs text-muted-foreground">Insert a variable</p>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="v in VARS" :key="v" type="button" class="rounded-md border bg-card px-2 py-1 font-mono text-xs hover:bg-muted" @click="insertVar(v)">{{ v }}</button>
          </div>
        </div>
        <div v-if="form.body" class="rounded-lg bg-success-soft/50 p-3 text-sm whitespace-pre-line sm:col-span-2">{{ preview }}</div>
        <label class="flex items-center gap-3 text-sm font-medium sm:col-span-2"><Switch :model-value="!!form.enabled" @update:model-value="form.enabled = $event ? 1 : 0" />Enabled</label>
      </form>
      <template #footer>
        <Button variant="outline" @click="open = false">Cancel</Button>
        <Button type="submit" form="tpl-form" :loading="save.pending.value">Save</Button>
      </template>
    </ModalDialog>
  </div>
</template>
