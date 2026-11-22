<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import '@/lib/chart'
import { useUiStore } from '@/stores/ui'
import { chartTheme, type ChartTheme } from '@/lib/chart'

/** Theme-aware ECharts wrapper. `build` receives the active theme tokens. */
const props = withDefaults(defineProps<{ build: (t: ChartTheme) => Record<string, unknown>; height?: number; label: string }>(), { height: 280 })
const ui = useUiStore()
const isDark = computed(() => ui.theme === 'dark' || (ui.theme === 'system' && typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches))
const option = computed(() => props.build(chartTheme(isDark.value)))
</script>

<template>
  <div role="img" :aria-label="label" :style="{ height: `${height}px` }" class="w-full">
    <VChart :option="option" autoresize class="size-full" />
  </div>
</template>
