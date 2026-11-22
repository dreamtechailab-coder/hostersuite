<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, BellRing, CheckCheck } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { notificationService } from '@/services/settings.service'
import { subscribeToPush } from '@/composables/usePwa'
import { useAuthStore } from '@/stores/auth'
import { relativeTime } from '@/utils/date'
import type { AppNotification } from '@/types'

const router = useRouter()
const auth = useAuthStore()
const items = ref<AppNotification[]>([])
const unread = ref(0)
const open = ref(false)
const loading = ref(false)
const pushSupported = typeof window !== 'undefined' && 'PushManager' in window && 'serviceWorker' in navigator

async function load() {
  if (document.visibilityState === 'hidden' || !navigator.onLine) return
  loading.value = true
  try {
    const res = await notificationService.list()
    items.value = res.data
    unread.value = res.unread
  } catch {
    /* non-critical */
  } finally {
    loading.value = false
  }
}
let timer: ReturnType<typeof setInterval>
onMounted(() => {
  load()
  timer = setInterval(load, 60_000)
})
onUnmounted(() => clearInterval(timer))

const ROUTES: Record<string, (n: string) => string> = {
  'PG Payment': (n) => `/payments/${n}`,
  'PG Rent Invoice': (n) => `/rent/invoices/${n}`,
  'PG Booking': () => '/bookings',
  'PG Occupancy': () => '/occupancy',
  'PG Tenant': (n) => `/tenants/${n}`,
}
async function openItem(n: AppNotification) {
  open.value = false
  if (!n.read) {
    n.read = 1
    unread.value = Math.max(0, unread.value - 1)
    notificationService.markRead(n.name).catch(() => {})
  }
  const to = n.document_type && n.document_name && ROUTES[n.document_type]?.(n.document_name)
  if (to) router.push(to)
}
async function markAll() {
  await notificationService.markRead()
  items.value.forEach((i) => (i.read = 1))
  unread.value = 0
}
async function enablePush() {
  try {
    const sub = await subscribeToPush(auth.settings?.vapid_public_key || '')
    if (!sub) return toast.info('Notifications were not enabled')
    await notificationService.savePush(sub.toJSON())
    toast.success('Push notifications enabled on this device')
  } catch (e) {
    toast.error((e as Error).message)
  }
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button variant="ghost" size="icon" class="relative" :aria-label="`Notifications${unread ? `, ${unread} unread` : ''}`">
        <Bell class="size-5" />
        <span v-if="unread" class="absolute right-1.5 top-1.5 flex min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold leading-4 text-white">
          {{ unread > 9 ? '9+' : unread }}
        </span>
      </Button>
    </PopoverTrigger>
    <PopoverContent align="end" class="w-[min(22rem,calc(100vw-1.5rem))] p-0">
      <div class="flex items-center justify-between border-b px-4 py-3">
        <p class="font-semibold">Notifications</p>
        <Button v-if="unread" variant="ghost" size="sm" @click="markAll"><CheckCheck />Mark all read</Button>
      </div>
      <ul class="max-h-96 overflow-y-auto">
        <li v-if="!items.length" class="px-4 py-10 text-center text-sm text-muted-foreground">You're all caught up</li>
        <li v-for="n in items" :key="n.name">
          <button type="button" class="flex w-full gap-3 px-4 py-3 text-left hover:bg-muted/60" @click="openItem(n)">
            <span :class="['mt-1.5 size-2 shrink-0 rounded-full', n.read ? 'bg-transparent' : 'bg-primary']" />
            <span class="min-w-0 flex-1">
              <span :class="['block text-sm', !n.read && 'font-medium']">{{ n.subject }}</span>
              <span class="text-xs text-muted-foreground">{{ relativeTime(n.creation) }}</span>
            </span>
          </button>
        </li>
      </ul>
      <div v-if="pushSupported && auth.settings?.vapid_public_key" class="border-t p-2">
        <Button variant="ghost" size="sm" class="w-full" @click="enablePush"><BellRing />Enable push on this device</Button>
      </div>
    </PopoverContent>
  </Popover>
</template>
