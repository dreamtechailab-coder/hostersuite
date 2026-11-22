<script setup lang="ts">
import { ref } from 'vue'
import { MailCheck } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import FormField from '@/components/common/FormField.vue'
import { authService } from '@/services/auth.service'
import { email as emailRule, required } from '@/utils/validation'

const email = ref('')
const error = ref('')
const sent = ref(false)
const loading = ref(false)

async function submit() {
  const r = required('Email')(email.value)
  const e = r === true ? emailRule(email.value, {}) : r
  if (e !== true) return (error.value = e)
  loading.value = true
  error.value = ''
  try {
    await authService.forgotPassword(email.value.trim())
  } catch {
    /* Don't reveal whether the account exists */
  } finally {
    loading.value = false
    sent.value = true
  }
}
</script>

<template>
  <div>
    <template v-if="!sent">
      <h1 class="text-2xl font-semibold tracking-tight">Forgot password?</h1>
      <p class="mt-1.5 text-sm text-muted-foreground">Enter your account email and we'll send you a link to reset it.</p>
      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <FormField v-slot="{ id, invalid }" label="Email" :error="error">
          <Input :id="id" v-model="email" type="email" autocomplete="email" :aria-invalid="invalid" autofocus />
        </FormField>
        <Button type="submit" size="lg" class="w-full" :loading="loading">Send reset link</Button>
      </form>
    </template>
    <div v-else class="text-center">
      <div class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-success-soft text-success"><MailCheck class="size-6" /></div>
      <h1 class="text-xl font-semibold">Check your email</h1>
      <p class="mt-2 text-sm text-muted-foreground">If an account exists for <strong>{{ email }}</strong>, a password reset link is on its way.</p>
    </div>
    <p class="mt-6 text-center text-sm">
      <RouterLink to="/login" class="font-medium text-primary hover:underline">Back to sign in</RouterLink>
    </p>
  </div>
</template>
