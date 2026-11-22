<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { NAV, type NavItem } from './nav'
import { useAuthStore } from '@/stores/auth'
import { cn } from '@/lib/utils'

const props = defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ navigate: [] }>()
const auth = useAuthStore()
const route = useRoute()

const allowed = (i: NavItem) => (i.perm ? auth.can(i.perm[0], i.perm[1]) : true) && (i.roles ? auth.hasRole(...i.roles) : true)
const groups = computed(() => NAV.map((g) => ({ ...g, items: g.items.filter(allowed) })).filter((g) => g.items.length))
const isActive = (i: NavItem) => (i.exact ? route.path === i.to : route.path === i.to || route.path.startsWith(i.to + '/'))
</script>

<template>
  <nav class="flex flex-col gap-5 px-3 py-4" aria-label="Main">
    <div v-for="g in groups" :key="g.label">
      <p v-if="!props.collapsed" class="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/80">{{ g.label }}</p>
      <div v-else class="mx-3 mb-2 h-px bg-border first:hidden" />
      <ul class="flex flex-col gap-0.5">
        <li v-for="item in g.items" :key="item.to">
          <RouterLink
            :to="item.to"
            :title="props.collapsed ? item.label : undefined"
            :aria-current="isActive(item) ? 'page' : undefined"
            :class="
              cn(
                'flex h-9 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40',
                isActive(item) && 'bg-accent text-accent-foreground',
                props.collapsed && 'justify-center px-0',
              )
            "
            @click="emit('navigate')"
          >
            <component :is="item.icon" :class="['size-[18px] shrink-0', isActive(item) && 'text-primary']" />
            <span v-if="!props.collapsed" class="truncate">{{ item.label }}</span>
          </RouterLink>
        </li>
      </ul>
    </div>
  </nav>
</template>
