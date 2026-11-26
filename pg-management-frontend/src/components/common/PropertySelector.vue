<script setup lang="ts">
import { Building2, Check, ChevronsUpDown } from 'lucide-vue-next'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { usePropertyStore } from '@/stores/property'
import { useAuthStore } from '@/stores/auth'

const store = usePropertyStore()
const auth = useAuthStore()
</script>

<template>
  <DropdownMenu v-if="auth.properties.length">
    <DropdownMenuTrigger
      class="flex h-10 min-w-0 max-w-[16rem] shrink items-center gap-2 rounded-lg border bg-card px-3 text-sm font-medium shadow-xs outline-none hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/40"
      aria-label="Select property"
    >
      <Building2 class="size-4 shrink-0 text-primary" />
      <span class="truncate">{{ store.label }}</span>
      <ChevronsUpDown class="size-3.5 shrink-0 text-muted-foreground" />
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start" class="max-h-80 w-[min(16rem,calc(100vw-2rem))] overflow-y-auto">
      <DropdownMenuLabel>Property</DropdownMenuLabel>
      <DropdownMenuItem v-if="auth.properties.length > 1" @select="store.select('')">
        <Check :class="['size-4', store.selected ? 'opacity-0' : '']" />
        All properties
      </DropdownMenuItem>
      <DropdownMenuSeparator v-if="auth.properties.length > 1" />
      <DropdownMenuItem v-for="p in store.options" :key="p.name" @select="store.select(p.name)">
        <Check :class="['size-4', store.selected === p.name ? '' : 'opacity-0']" />
        <span class="min-w-0 flex-1 truncate">{{ p.property_name }}</span>
        <span v-if="p.city" class="text-xs text-muted-foreground">{{ p.city }}</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
