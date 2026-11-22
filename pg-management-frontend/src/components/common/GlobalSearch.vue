<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { watchDebounced, useMagicKeys, whenever } from '@vueuse/core'
import { Building2, DoorOpen, FileText, Loader2, Search, User, CalendarCheck } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { searchService } from '@/services/settings.service'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const router = useRouter()
const q = ref('')
const loading = ref(false)
const results = ref<{ type: string; name: string; title: string; subtitle?: string }[]>([])
const active = ref(0)

const keys = useMagicKeys({
  passive: false,
  onEventFired(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k' && e.type === 'keydown') e.preventDefault()
  },
})
whenever(keys['Meta+K'], () => (ui.searchOpen = true))
whenever(keys['Ctrl+K'], () => (ui.searchOpen = true))

watch(() => ui.searchOpen, (o) => {
  if (!o) {
    q.value = ''
    results.value = []
  }
})
watchDebounced(
  q,
  async (v) => {
    if (v.trim().length < 2) return (results.value = [])
    loading.value = true
    try {
      results.value = await searchService.search(v)
      active.value = 0
    } catch {
      results.value = []
    } finally {
      loading.value = false
    }
  },
  { debounce: 250 },
)
const ICONS: Record<string, any> = { tenant: User, room: DoorOpen, property: Building2, invoice: FileText, booking: CalendarCheck }
const LINKS: Record<string, (n: string) => string> = {
  tenant: (n) => `/tenants/${n}`,
  room: (n) => `/rooms/${n}`,
  property: (n) => `/properties/${encodeURIComponent(n)}`,
  invoice: (n) => `/rent/invoices/${n}`,
  booking: () => `/bookings`,
}
function go(r: { type: string; name: string }) {
  ui.searchOpen = false
  router.push(LINKS[r.type]?.(r.name) || '/')
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') active.value = Math.min(results.value.length - 1, active.value + 1)
  else if (e.key === 'ArrowUp') active.value = Math.max(0, active.value - 1)
  else if (e.key === 'Enter' && results.value[active.value]) go(results.value[active.value])
  else return
  e.preventDefault()
}
</script>

<template>
  <Dialog v-model:open="ui.searchOpen">
    <DialogContent class="top-4 bottom-auto rounded-xl sm:top-[15%] sm:translate-y-0" hide-close>
      <DialogTitle class="sr-only">Search</DialogTitle>
      <DialogDescription class="sr-only">Search tenants, rooms, properties, invoices and bookings</DialogDescription>
      <div class="flex items-center gap-3 border-b px-4">
        <Search class="size-5 text-muted-foreground" />
        <input
          v-model="q"
          class="h-14 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
          placeholder="Search tenants, rooms, invoices…"
          aria-label="Search"
          autofocus
          @keydown="onKey"
        />
        <Loader2 v-if="loading" class="size-4 animate-spin text-muted-foreground" />
        <kbd class="hidden rounded border px-1.5 text-[11px] text-muted-foreground sm:block">Esc</kbd>
      </div>
      <ul class="max-h-[60vh] overflow-y-auto p-2">
        <li v-if="q.length >= 2 && !loading && !results.length" class="py-10 text-center text-sm text-muted-foreground">No results for “{{ q }}”</li>
        <li v-if="q.length < 2" class="py-8 text-center text-sm text-muted-foreground">Type at least 2 characters</li>
        <li v-for="(r, i) in results" :key="`${r.type}-${r.name}`">
          <button
            type="button"
            :class="['flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left', i === active ? 'bg-accent' : 'hover:bg-muted']"
            @mouseenter="active = i"
            @click="go(r)"
          >
            <span class="flex size-8 items-center justify-center rounded-md bg-muted text-muted-foreground"><component :is="ICONS[r.type] || Search" class="size-4" /></span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm font-medium">{{ r.title }}</span>
              <span class="block truncate text-xs capitalize text-muted-foreground">{{ r.type }} · {{ r.subtitle || r.name }}</span>
            </span>
          </button>
        </li>
      </ul>
    </DialogContent>
  </Dialog>
</template>
