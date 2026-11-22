<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, Lock, WifiOff, SearchX } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/services/api'

const props = defineProps<{ error?: Error | null; title?: string; compact?: boolean }>()
const emit = defineEmits<{ retry: [] }>()

const kind = computed(() => {
  const e = props.error
  if (e instanceof ApiError) {
    if (e.offline) return 'offline'
    if (e.isPermission) return 'forbidden'
    if (e.isNotFound) return 'notfound'
  }
  return 'error'
})
const meta = computed(
  () =>
    ({
      offline: { icon: WifiOff, title: "You're offline", text: 'Reconnect to load live data. Nothing is saved while offline.' },
      forbidden: { icon: Lock, title: 'No access', text: props.error?.message || 'You do not have permission to view this.' },
      notfound: { icon: SearchX, title: 'Not found', text: props.error?.message || 'This record does not exist or was removed.' },
      error: { icon: AlertTriangle, title: props.title || "Couldn't load this", text: props.error?.message || 'Something went wrong.' },
    })[kind.value],
)
</script>

<template>
  <div role="alert" :class="['flex flex-col items-center justify-center text-center', compact ? 'px-4 py-8' : 'px-6 py-14']">
    <div
      :class="[
        'mb-3 flex size-12 items-center justify-center rounded-full',
        kind === 'error' ? 'bg-danger-soft text-destructive' : 'bg-muted text-muted-foreground',
      ]"
    >
      <component :is="meta.icon" class="size-5" />
    </div>
    <p class="font-medium">{{ meta.title }}</p>
    <p class="mt-1 max-w-sm whitespace-pre-line text-sm text-muted-foreground">{{ meta.text }}</p>
    <Button v-if="kind !== 'forbidden' && kind !== 'notfound'" variant="outline" size="sm" class="mt-4" @click="emit('retry')">Try again</Button>
  </div>
</template>
