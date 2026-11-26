<script setup lang="ts">
import { computed } from 'vue'
import { Download, LogOut, Menu, Monitor, Moon, Search, Sun, LayoutGrid } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import { Avatar } from '@/components/ui/avatar'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import PropertySelector from '@/components/common/PropertySelector.vue'
import NotificationCenter from '@/components/common/NotificationCenter.vue'
import { useUiStore } from '@/stores/ui'
import { useAuth } from '@/composables/useAuth'
import { usePwaInstall } from '@/composables/usePwa'

const ui = useUiStore()
const { user, roles, logout } = useAuth()
// PG users without System Manager are redirected away from Desk by the backend
const canUseDesk = computed(() => user.value?.user === 'Administrator' || roles.value.includes('System Manager'))
const { canInstall, hasPrompt, isIos, install } = usePwaInstall()

async function onInstall() {
  if (hasPrompt.value) await install()
  else if (isIos) toast.info('To install: tap the Share button, then “Add to Home Screen”.', { duration: 8000 })
}
</script>

<template>
  <header class="sticky top-0 z-30 border-b bg-background/85 backdrop-blur supports-[backdrop-filter]:bg-background/70" style="padding-top: env(safe-area-inset-top)">
    <div class="flex h-16 items-center gap-2 px-4 sm:px-6">
      <Button variant="ghost" size="icon" class="-ml-2 lg:hidden" aria-label="Open navigation" @click="ui.mobileNavOpen = true">
        <Menu class="size-5" />
      </Button>
      <PropertySelector />

      <button
        type="button"
        class="ml-auto flex h-10 shrink-0 items-center gap-2 rounded-lg border bg-card px-3 text-sm text-muted-foreground shadow-xs transition hover:text-foreground md:ml-4 md:w-72"
        aria-label="Search"
        @click="ui.searchOpen = true"
      >
        <Search class="size-4" />
        <span class="hidden md:inline">Search…</span>
        <kbd class="ml-auto hidden rounded border px-1.5 text-[11px] md:inline">⌘K</kbd>
      </button>

      <div class="flex shrink-0 items-center gap-1 md:ml-auto">
        <NotificationCenter />
        <DropdownMenu>
          <DropdownMenuTrigger class="rounded-full outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40" aria-label="Account menu">
            <Avatar :name="user?.full_name" :src="user?.user_image" />
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-60">
            <div class="px-2 py-2">
              <p class="truncate text-sm font-medium">{{ user?.full_name }}</p>
              <p class="truncate text-xs text-muted-foreground">{{ user?.email }}</p>
              <p class="mt-1 truncate text-[11px] text-muted-foreground">{{ user?.roles?.join(' · ') }}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Theme</DropdownMenuLabel>
            <div class="grid grid-cols-3 gap-1 px-1 pb-1">
              <button
                v-for="t in [{ v: 'light', i: Sun }, { v: 'dark', i: Moon }, { v: 'system', i: Monitor }] as const"
                :key="t.v"
                type="button"
                :class="['flex h-8 items-center justify-center rounded-md text-xs capitalize', ui.theme === t.v ? 'bg-accent text-accent-foreground' : 'hover:bg-muted']"
                :aria-pressed="ui.theme === t.v"
                @click="ui.theme = t.v"
              >
                <component :is="t.i" class="size-4" />
              </button>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem v-if="canInstall" @select="onInstall"><Download />Install app</DropdownMenuItem>
            <DropdownMenuItem v-if="canUseDesk" as="a" href="/app" target="_blank"><LayoutGrid />Admin desk</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem destructive @select="logout"><LogOut />Log out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  </header>
</template>
