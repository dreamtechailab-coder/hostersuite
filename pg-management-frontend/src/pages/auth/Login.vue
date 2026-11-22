<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff, AlertCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import FormField from '@/components/common/FormField.vue'
import { useAuthStore } from '@/stores/auth'
import { required, validate } from '@/utils/validation'

const BACKEND_PATH = /^\/(app|desk|files|private|api)(\/|$|\?)/
// never "return" to an auth page after signing in – go to the dashboard instead
const AUTH_PATH = /^\/(login|forgot-password|update-password|reset-password)(\/|$|\?)/

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const errors = ref<Record<string, string>>({})
const error = ref(route.query.expired ? 'Your session expired. Please sign in again.' : '')
const loading = ref(false)
const show = ref(false)

async function submit() {
  errors.value = validate(form, { username: [required('Email or username')], password: [required('Password')] })
  if (Object.keys(errors.value).length) return
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.username, form.password)
    const q = route.query.redirect
    const redirect = typeof q === 'string' && q.startsWith('/') && !q.startsWith('//') && q !== '/' && !AUTH_PATH.test(q) ? q : null
    // Targets served by Frappe (e.g. /app from the Desk) need a full page load.
    if (redirect && BACKEND_PATH.test(redirect)) window.location.assign(redirect)
    else await router.replace(redirect || { name: 'dashboard' })
  } catch (e) {
    error.value = (e as Error).message || 'Invalid login credentials'
    form.password = ''
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-[1.75rem] font-semibold leading-tight tracking-[-0.02em]">Sign in</h1>
    <p class="mt-2 text-sm text-muted-foreground">Use the email and password your HostelSuite admin set up for you.</p>

    <div v-if="error" role="alert" class="mt-6 flex gap-2 rounded-lg border border-destructive/20 bg-danger-soft px-3 py-2.5 text-sm text-destructive">
      <AlertCircle class="mt-0.5 size-4 shrink-0" />{{ error }}
    </div>

    <form class="mt-8 space-y-5" novalidate @submit.prevent="submit">
      <FormField v-slot="{ id, invalid }" label="Email or username" :error="errors.username">
        <Input :id="id" v-model="form.username" autocomplete="username" inputmode="email" autocapitalize="none" :aria-invalid="invalid" autofocus />
      </FormField>
      <FormField v-slot="{ id, invalid }" label="Password" :error="errors.password">
        <div class="relative">
          <Input :id="id" v-model="form.password" :type="show ? 'text' : 'password'" autocomplete="current-password" :aria-invalid="invalid" class="pr-10" />
          <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-muted-foreground hover:text-foreground" :aria-label="show ? 'Hide password' : 'Show password'" @click="show = !show">
            <EyeOff v-if="show" class="size-4" /><Eye v-else class="size-4" />
          </button>
        </div>
      </FormField>
      <div class="flex justify-end">
        <RouterLink to="/forgot-password" class="text-sm font-medium text-primary hover:underline">Forgot password?</RouterLink>
      </div>
      <Button type="submit" size="lg" class="w-full" :loading="loading">Sign in</Button>
    </form>
  </div>
</template>
