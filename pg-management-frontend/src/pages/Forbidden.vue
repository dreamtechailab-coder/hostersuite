<script setup lang="ts">
import { Lock } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import EmptyState from '@/components/common/EmptyState.vue'
</script>
<template>
  <EmptyState :icon="Lock" title="You don't have access to this page" description="Ask your administrator to grant the required role or property access.">
    <Button as-child><RouterLink to="/">Go to dashboard</RouterLink></Button>
  </EmptyState>
</template>
