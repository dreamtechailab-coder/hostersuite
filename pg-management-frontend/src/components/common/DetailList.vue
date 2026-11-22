<script setup lang="ts">
defineProps<{ items: { label: string; value?: string | number | null; key?: string }[]; cols?: 1 | 2 | 3 }>()
</script>
<template>
  <dl :class="['grid gap-x-6 gap-y-4', cols === 1 ? '' : cols === 3 ? 'grid-cols-2 lg:grid-cols-3' : 'grid-cols-2']">
    <div v-for="item in items" :key="item.key || item.label" class="min-w-0">
      <dt class="text-xs text-muted-foreground">{{ item.label }}</dt>
      <dd class="mt-0.5 truncate text-sm font-medium">
        <slot :name="item.key || item.label" :item="item">{{ item.value ?? '—' }}</slot>
      </dd>
    </div>
  </dl>
</template>
