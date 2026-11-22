<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
const route = useRoute()
const links = [
  { to: '/settings/general', label: 'General' },
  { to: '/settings/users', label: 'Users' },
  { to: '/settings/roles', label: 'Roles' },
  { to: '/settings/whatsapp', label: 'WhatsApp' },
]
</script>
<template>
  <nav class="mb-5 flex gap-1 overflow-x-auto border-b" aria-label="Settings">
    <RouterLink
      v-for="l in links"
      :key="l.to"
      :to="l.to"
      :class="['-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition', route.path === l.to ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground']"
    >
      {{ l.label }}
    </RouterLink>
  </nav>
</template>
