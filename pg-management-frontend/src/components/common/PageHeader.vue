<script setup lang="ts">
import { ChevronLeft } from 'lucide-vue-next'
import { useRouter, type RouteLocationRaw } from 'vue-router'

const props = defineProps<{ title: string; description?: string; back?: RouteLocationRaw | boolean }>()
const router = useRouter()
function goBack() {
  if (typeof props.back === 'object' || typeof props.back === 'string') router.push(props.back)
  else router.back()
}
</script>

<template>
  <header class="mb-5 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-end sm:justify-between">
    <div class="flex min-w-0 items-start gap-2">
      <button
        v-if="back"
        type="button"
        class="-ml-1.5 mt-0.5 rounded-md p-1.5 text-muted-foreground transition hover:bg-muted hover:text-foreground"
        aria-label="Go back"
        @click="goBack"
      >
        <ChevronLeft class="size-5" />
      </button>
      <div class="min-w-0">
        <div class="flex flex-wrap items-center gap-2">
          <h1 class="truncate text-xl font-semibold tracking-tight sm:text-2xl">{{ title }}</h1>
          <slot name="badge" />
        </div>
        <p v-if="description || $slots.description" class="mt-1 text-sm text-muted-foreground">
          <slot name="description">{{ description }}</slot>
        </p>
      </div>
    </div>
    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2 sm:justify-end">
      <slot name="actions" />
    </div>
  </header>
</template>
