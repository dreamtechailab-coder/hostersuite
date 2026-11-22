<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import SearchSelect from '@/components/common/SearchSelect.vue'
import FileUploader from '@/components/common/FileUploader.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { expenseService } from '@/services/payment.service'
import { useMutation } from '@/composables/useMutation'
import { useConfirm } from '@/composables/useConfirm'
import { usePermissions } from '@/composables/usePermissions'
import { usePropertyStore } from '@/stores/property'
import { useDashboardStore } from '@/stores/dashboard'
import { positive, required, validate } from '@/utils/validation'
import { today } from '@/utils/date'
import type { Expense } from '@/types'

const props = defineProps<{ name?: string }>()
const router = useRouter()
const property = usePropertyStore()
const dashboard = useDashboardStore()
const { can } = usePermissions()
const { confirm } = useConfirm()
const form = reactive<Partial<Expense>>({ property: property.filter || '', category: '', expense_date: today(), amount: undefined, vendor: '', payment_status: 'Paid', due_date: '', paid_on: '', payment_mode: 'UPI', description: '', attachment: '' })
const errors = ref<Record<string, string>>({})
const loading = ref(!!props.name)
const loadError = ref<Error | null>(null)
onMounted(async () => {
  if (!props.name) return
  try {
    Object.assign(form, (await expenseService.get(props.name)).data)
  } catch (e) {
    loadError.value = e as Error
  } finally {
    loading.value = false
  }
})
const save = useMutation(expenseService.save, { success: 'Expense saved' })
const del = useMutation(() => expenseService.remove(props.name!), { success: 'Expense deleted' })
async function submit() {
  errors.value = validate(form, { property: [required('Property')], category: [required('Category')], expense_date: [required('Date')], amount: [required('Amount'), positive('Amount')] })
  if (Object.keys(errors.value).length) return
  if (await save.run(form)) {
    dashboard.invalidate()
    router.replace('/expenses')
  }
}
async function remove() {
  const { confirmed } = await confirm({ title: 'Delete this expense?', destructive: true, confirmText: 'Delete' })
  if (confirmed && (await del.run())) {
    dashboard.invalidate()
    router.replace('/expenses')
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <PageHeader :title="name ? 'Edit expense' : 'Add expense'" back="/expenses">
      <template v-if="name && can('PG Expense', 'delete')" #actions><Button variant="outline" @click="remove"><Trash2 />Delete</Button></template>
    </PageHeader>
    <ErrorState v-if="loadError" :error="loadError" />
    <LoadingSkeleton v-else-if="loading" variant="form" />
    <Card v-else>
      <CardContent>
        <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="submit">
          <FormField v-slot="{ id, invalid }" label="Amount" required :error="errors.amount" class="sm:col-span-2">
            <Input :id="id" v-model.number="form.amount" type="number" min="0" step="0.01" inputmode="decimal" class="h-12 text-lg font-semibold" :aria-invalid="invalid" />
          </FormField>
          <FormField v-slot="{ id, invalid }" label="Property" required :error="errors.property"><SearchSelect :id="id" v-model="form.property" doctype="PG Property" :invalid="invalid" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Category" required :error="errors.category"><SearchSelect :id="id" v-model="form.category" doctype="PG Expense Category" :invalid="invalid" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Date" required :error="errors.expense_date"><Input :id="id" v-model="form.expense_date" type="date" :aria-invalid="invalid" /></FormField>
          <FormField v-slot="{ id }" label="Vendor / payee"><Input :id="id" v-model="form.vendor" /></FormField>
          <FormField v-slot="{ id }" label="Status"><NativeSelect :id="id" v-model="form.payment_status" :options="['Paid', 'Unpaid']" /></FormField>
          <FormField v-if="form.payment_status === 'Paid'" v-slot="{ id }" label="Paid via"><NativeSelect :id="id" v-model="form.payment_mode" :options="['Cash', 'UPI', 'Bank Transfer', 'Card', 'Cheque']" /></FormField>
          <FormField v-else v-slot="{ id }" label="Due date"><Input :id="id" v-model="form.due_date" type="date" /></FormField>
          <FormField v-slot="{ id }" label="Description" class="sm:col-span-2"><Textarea :id="id" v-model="form.description" rows="2" /></FormField>
          <FormField label="Bill / receipt" class="sm:col-span-2"><FileUploader v-model="form.attachment" :doctype="name ? 'PG Expense' : undefined" :docname="name" fieldname="attachment" /></FormField>
          <div class="flex justify-end gap-2 sm:col-span-2">
            <Button variant="outline" @click="router.back()">Cancel</Button>
            <Button type="submit" :loading="save.pending.value">Save expense</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
