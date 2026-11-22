<script setup lang="ts">
import { TabsRoot } from 'reka-ui'
const model = defineModel<string | number>()
</script>
<template>
  <TabsRoot v-model="model" class="flex flex-col gap-4"><slot /></TabsRoot>
</template>
