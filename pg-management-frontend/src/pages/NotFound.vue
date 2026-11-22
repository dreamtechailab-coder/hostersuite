<script setup lang="ts">
import { Button } from '@/components/ui/button'
</script>
<template>
  <div class="flex min-h-dvh flex-col items-center justify-center px-4 text-center">
    <p class="text-6xl font-semibold tracking-tight text-primary">404</p>
    <h1 class="mt-4 text-xl font-semibold">Page not found</h1>
    <p class="mt-2 text-sm text-muted-foreground">The page you're looking for doesn't exist or has moved.</p>
    <Button as-child class="mt-6"><RouterLink to="/">Back to dashboard</RouterLink></Button>
  </div>
</template>
