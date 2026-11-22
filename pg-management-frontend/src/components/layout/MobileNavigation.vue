<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { CreditCard, DoorOpen, LayoutDashboard, Menu, Users } from 'lucide-vue-next'
import { Sheet, SheetContent, SheetDescription, SheetTitle } from '@/components/ui/sheet'
import SidebarNav from './SidebarNav.vue'
import AppLogo from './AppLogo.vue'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

const ui = useUiStore()
const auth = useAuthStore()
const route = useRoute()

const tabs = computed(() =>
  [
    { label: 'Home', to: '/', icon: LayoutDashboard, show: true, exact: true },
    { label: 'Rooms', to: '/rooms', icon: DoorOpen, show: auth.can('PG Room') },
    { label: 'Tenants', to: '/tenants', icon: Users, show: auth.can('PG Tenant') },
    { label: 'Collect', to: '/payments/collect', icon: CreditCard, show: auth.can('PG Payment', 'create') },
  ].filter((t) => t.show),
)
const active = (t: { to: string; exact?: boolean }) => (t.exact ? route.path === t.to : route.path.startsWith(t.to))
</script>

<template>
  <!-- bottom tab bar -->
  <nav class="fixed inset-x-0 bottom-0 z-40 border-t bg-card/95 backdrop-blur lg:hidden safe-bottom" aria-label="Quick navigation">
    <ul class="mx-auto grid max-w-lg" :style="{ gridTemplateColumns: `repeat(${tabs.length + 1}, minmax(0, 1fr))` }">
      <li v-for="t in tabs" :key="t.to">
        <RouterLink
          :to="t.to"
          :aria-current="active(t) ? 'page' : undefined"
          :class="['flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium', active(t) ? 'text-primary' : 'text-muted-foreground']"
        >
          <component :is="t.icon" class="size-5" />
          {{ t.label }}
        </RouterLink>
      </li>
      <li>
        <button type="button" class="flex h-16 w-full flex-col items-center justify-center gap-1 text-[11px] font-medium text-muted-foreground" @click="ui.mobileNavOpen = true">
          <Menu class="size-5" />More
        </button>
      </li>
    </ul>
  </nav>

  <!-- slide-out drawer -->
  <Sheet v-model:open="ui.mobileNavOpen">
    <SheetContent side="left" class="p-0">
      <SheetTitle class="sr-only">Navigation</SheetTitle>
      <SheetDescription class="sr-only">All sections</SheetDescription>
      <div class="flex h-16 items-center border-b px-5"><AppLogo /></div>
      <div class="flex-1 overflow-y-auto"><SidebarNav @navigate="ui.mobileNavOpen = false" /></div>
    </SheetContent>
  </Sheet>
</template>
