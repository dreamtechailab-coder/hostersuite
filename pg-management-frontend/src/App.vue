<script setup lang="ts">
import { Toaster } from 'vue-sonner'
import 'vue-sonner/style.css'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import PwaPrompts from '@/components/common/PwaPrompts.vue'
import { useUiStore } from '@/stores/ui'
import { computed } from 'vue'

const ui = useUiStore()
const toastTheme = computed(() => (ui.theme === 'system' ? 'system' : ui.theme))
</script>

<template>
  <RouterView />
  <ConfirmationDialog />
  <PwaPrompts />
  <Toaster position="top-center" rich-colors close-button :theme="toastTheme" :toast-options="{ class: 'font-sans' }" />
</template>
