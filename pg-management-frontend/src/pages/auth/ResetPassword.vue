<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { watchDebounced } from '@vueuse/core'
import { CheckCircle2, AlertCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import FormField from '@/components/common/FormField.vue'
import { authService } from '@/services/auth.service'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const key = computed(() => (typeof route.query.key === 'string' ? route.query.key : ''))
const password = ref('')
const confirm = ref('')
const errors = ref<Record<string, string>>({})
const error = ref('')
const done = ref(false)
const loading = ref(false)
const score = ref<number | null>(null)
const feedback = ref('')

watchDebounced(
  password,
  async (v) => {
    if (v.length < 6) return (score.value = null)
    try {
      const r = await authService.passwordStrength(v)
      score.value = r.score
      feedback.value = r.feedback?.warning || r.feedback?.suggestions?.[0] || ''
    } catch {
      score.value = null
    }
  },
  { debounce: 400 },
)
const strength = computed(() => ['Very weak', 'Weak', 'Fair', 'Good', 'Strong'][score.value ?? 0])

async function submit() {
  errors.value = {}
  if (password.value.length < 8) errors.value.password = 'Use at least 8 characters'
  if (password.value !== confirm.value) errors.value.confirm = 'Passwords do not match'
  if (Object.keys(errors.value).length) return
  loading.value = true
  error.value = ''
  try {
    await authService.resetPassword(key.value, password.value)
    done.value = true
    await auth.refresh()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div v-if="!key" class="text-center">
      <AlertCircle class="mx-auto mb-3 size-10 text-destructive" />
      <h1 class="text-xl font-semibold">Invalid reset link</h1>
      <p class="mt-2 text-sm text-muted-foreground">This link is missing its key or has expired. Request a new one.</p>
      <Button as="a" :href="router.resolve('/forgot-password').href" class="mt-5">Request new link</Button>
    </div>
    <div v-else-if="done" class="text-center">
      <CheckCircle2 class="mx-auto mb-3 size-10 text-success" />
      <h1 class="text-xl font-semibold">Password updated</h1>
      <p class="mt-2 text-sm text-muted-foreground">You can now use your new password.</p>
      <Button class="mt-5" @click="router.replace(auth.isLoggedIn ? '/' : '/login')">Continue</Button>
    </div>
    <template v-else>
      <h1 class="text-2xl font-semibold tracking-tight">Set a new password</h1>
      <p class="mt-1.5 text-sm text-muted-foreground">Choose a strong password you don't use elsewhere.</p>
      <div v-if="error" role="alert" class="mt-5 rounded-lg bg-danger-soft px-3 py-2.5 text-sm text-destructive">{{ error }}</div>
      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <FormField v-slot="{ id, invalid }" label="New password" :error="errors.password">
          <Input :id="id" v-model="password" type="password" autocomplete="new-password" :aria-invalid="invalid" />
        </FormField>
        <div v-if="score !== null" class="-mt-2">
          <div class="flex gap-1">
            <span v-for="i in 4" :key="i" :class="['h-1 flex-1 rounded-full', i <= (score || 0) ? (score! >= 3 ? 'bg-success' : score! >= 2 ? 'bg-warning' : 'bg-destructive') : 'bg-muted']" />
          </div>
          <p class="mt-1 text-xs text-muted-foreground">{{ strength }}<span v-if="feedback"> – {{ feedback }}</span></p>
        </div>
        <FormField v-slot="{ id, invalid }" label="Confirm password" :error="errors.confirm">
          <Input :id="id" v-model="confirm" type="password" autocomplete="new-password" :aria-invalid="invalid" />
        </FormField>
        <Button type="submit" size="lg" class="w-full" :loading="loading">Update password</Button>
      </form>
    </template>
  </div>
</template>
