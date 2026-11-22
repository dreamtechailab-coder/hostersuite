<script setup lang="ts">
import { PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'
import AppLogo from './AppLogo.vue'
import SidebarNav from './SidebarNav.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
</script>

<template>
  <aside
    :class="[
      'sticky top-0 hidden h-dvh shrink-0 flex-col border-r bg-sidebar transition-[width] duration-200 lg:flex',
      ui.sidebarCollapsed ? 'w-[72px]' : 'w-64',
    ]"
  >
    <div :class="['flex h-16 items-center border-b', ui.sidebarCollapsed ? 'justify-center px-2' : 'px-5']">
      <AppLogo :collapsed="ui.sidebarCollapsed" />
    </div>
    <div class="flex-1 overflow-y-auto"><SidebarNav :collapsed="ui.sidebarCollapsed" /></div>
    <button
      type="button"
      class="flex h-12 items-center gap-2 border-t px-5 text-sm text-muted-foreground hover:text-foreground"
      :class="ui.sidebarCollapsed && 'justify-center px-0'"
      :aria-label="ui.sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      @click="ui.sidebarCollapsed = !ui.sidebarCollapsed"
    >
      <PanelLeftOpen v-if="ui.sidebarCollapsed" class="size-4" />
      <template v-else><PanelLeftClose class="size-4" />Collapse</template>
    </button>
  </aside>
</template>
