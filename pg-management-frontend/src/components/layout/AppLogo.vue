<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const logoUrl = `${import.meta.env.BASE_URL}icons/logo.svg`
defineProps<{ collapsed?: boolean }>()
const auth = useAuthStore()
</script>
<template>
  <div class="flex min-w-0 items-center gap-2.5">
    <img :src="logoUrl" alt="" class="size-8 shrink-0 rounded-lg" />
    <div v-if="!collapsed" class="min-w-0 leading-tight">
      <p class="truncate text-[15px] font-semibold tracking-tight">HostelSuite</p>
      <p class="truncate text-[11px] text-muted-foreground">{{ auth.settings?.organization_name }}</p>
    </div>
  </div>
</template>
