<script setup lang="ts">
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

const props = defineProps<{ title: string; description?: string; size?: 'sm' | 'md' | 'lg' | 'xl' }>()
const open = defineModel<boolean>('open', { default: false })
const sizes = { sm: 'sm:max-w-sm', md: 'sm:max-w-lg', lg: 'sm:max-w-2xl', xl: 'sm:max-w-4xl' }
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent :class="cn(sizes[props.size || 'md'])">
      <div class="border-b px-5 pb-4 pt-5 pr-12">
        <DialogTitle class="text-base font-semibold">{{ title }}</DialogTitle>
        <DialogDescription v-if="description" class="mt-1 text-sm text-muted-foreground">{{ description }}</DialogDescription>
        <DialogDescription v-else class="sr-only">{{ title }}</DialogDescription>
      </div>
      <div class="flex-1 overflow-y-auto px-5 py-4"><slot /></div>
      <div v-if="$slots.footer" class="flex flex-col-reverse gap-2 border-t bg-muted/30 px-5 py-3 safe-bottom sm:flex-row sm:justify-end">
        <slot name="footer" />
      </div>
    </DialogContent>
  </Dialog>
</template>
