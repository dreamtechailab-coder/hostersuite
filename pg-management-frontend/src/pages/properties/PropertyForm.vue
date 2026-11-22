<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { NativeSelect } from '@/components/ui/select'
import PageHeader from '@/components/common/PageHeader.vue'
import FormField from '@/components/common/FormField.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { propertyService } from '@/services/property.service'
import { useMutation } from '@/composables/useMutation'
import { useAuthStore } from '@/stores/auth'
import { email, mobile, required, validate } from '@/utils/validation'
import type { Property } from '@/types'

const props = defineProps<{ name?: string }>()
const router = useRouter()
const auth = useAuthStore()
const form = reactive<Partial<Property>>({ property_name: '', property_code: '', property_type: 'Co-living', is_active: 1, city: '', state: '', pincode: '', address_line: '', phone: '', email: '', amenities: '', notes: '' })
const errors = ref<Record<string, string>>({})
const loading = ref(!!props.name)
const loadError = ref<Error | null>(null)

onMounted(async () => {
  if (!props.name) return
  try {
    Object.assign(form, (await propertyService.get(props.name)).data)
  } catch (e) {
    loadError.value = e as Error
  } finally {
    loading.value = false
  }
})
const save = useMutation(propertyService.save, { success: 'Property saved' })
async function submit() {
  errors.value = validate(form, { property_name: [required('Property name')], phone: [mobile], email: [email] })
  if (Object.keys(errors.value).length) return
  const res = await save.run(form)
  if (res) {
    await auth.refresh() // property list in session/selector
    router.replace(`/properties/${encodeURIComponent(res.data.name)}`)
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <PageHeader :title="name ? 'Edit property' : 'New property'" back />
    <ErrorState v-if="loadError" :error="loadError" />
    <LoadingSkeleton v-else-if="loading" variant="form" />
    <form v-else class="space-y-5" novalidate @submit.prevent="submit">
      <Card>
        <CardHeader><CardTitle>Basic details</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2">
          <FormField v-slot="{ id, invalid }" label="Property name" required :error="errors.property_name" class="sm:col-span-2">
            <Input :id="id" v-model="form.property_name" :aria-invalid="invalid" :disabled="!!name" placeholder="e.g. Sunrise PG Koramangala" />
          </FormField>
          <FormField v-slot="{ id }" label="Short code" hint="Optional, e.g. KRM-01"><Input :id="id" v-model="form.property_code" /></FormField>
          <FormField v-slot="{ id }" label="Type"><NativeSelect :id="id" v-model="form.property_type" :options="['Boys', 'Girls', 'Co-living']" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Phone" :error="errors.phone"><Input :id="id" v-model="form.phone" type="tel" inputmode="tel" :aria-invalid="invalid" /></FormField>
          <FormField v-slot="{ id, invalid }" label="Email" :error="errors.email"><Input :id="id" v-model="form.email" type="email" :aria-invalid="invalid" /></FormField>
          <label class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium sm:col-span-2">
            Active – accepting tenants
            <Switch :model-value="!!form.is_active" @update:model-value="form.is_active = $event ? 1 : 0" />
          </label>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Address</CardTitle></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-3">
          <FormField v-slot="{ id }" label="Street address" class="sm:col-span-3"><Textarea :id="id" v-model="form.address_line" rows="2" /></FormField>
          <FormField v-slot="{ id }" label="City"><Input :id="id" v-model="form.city" /></FormField>
          <FormField v-slot="{ id }" label="State"><Input :id="id" v-model="form.state" /></FormField>
          <FormField v-slot="{ id }" label="PIN code"><Input :id="id" v-model="form.pincode" inputmode="numeric" /></FormField>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>More</CardTitle></CardHeader>
        <CardContent class="grid gap-4">
          <FormField v-slot="{ id }" label="Amenities" hint="Wi-Fi, laundry, meals…"><Textarea :id="id" v-model="form.amenities" rows="2" /></FormField>
          <FormField v-slot="{ id }" label="Internal notes"><Textarea :id="id" v-model="form.notes" rows="3" /></FormField>
        </CardContent>
      </Card>
      <div class="sticky bottom-20 flex justify-end gap-2 rounded-xl border bg-card/95 p-3 backdrop-blur lg:bottom-4">
        <Button variant="outline" @click="router.back()">Cancel</Button>
        <Button type="submit" :loading="save.pending.value">Save property</Button>
      </div>
    </form>
  </div>
</template>
