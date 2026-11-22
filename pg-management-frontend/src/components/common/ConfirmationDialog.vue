<script setup lang="ts">
import { AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogOverlay, AlertDialogPortal, AlertDialogRoot, AlertDialogTitle } from 'reka-ui'
import { AlertTriangle } from 'lucide-vue-next'
import { buttonVariants } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useConfirmState } from '@/composables/useConfirm'

const { state, close } = useConfirmState()
function onOpen(v: boolean) {
  if (!v && state.open) close(false)
}
</script>

<template>
  <AlertDialogRoot :open="state.open" @update:open="onOpen">
    <AlertDialogPortal>
      <AlertDialogOverlay class="fixed inset-0 z-50 bg-slate-950/40 data-[state=open]:animate-in data-[state=open]:fade-in-0" />
      <AlertDialogContent
        class="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-card p-5 shadow-xl data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95"
      >
        <div class="flex gap-3">
          <div
            :class="[
              'flex size-10 shrink-0 items-center justify-center rounded-full',
              state.options.destructive ? 'bg-danger-soft text-destructive' : 'bg-primary/10 text-primary',
            ]"
          >
            <AlertTriangle class="size-5" />
          </div>
          <div class="min-w-0 flex-1">
            <AlertDialogTitle class="font-semibold">{{ state.options.title }}</AlertDialogTitle>
            <AlertDialogDescription class="mt-1 text-sm text-muted-foreground">
              {{ state.options.description || 'Are you sure you want to continue?' }}
            </AlertDialogDescription>
          </div>
        </div>
        <div v-if="state.options.withReason" class="mt-4">
          <label class="mb-1.5 block text-[13px] font-medium" for="confirm-reason">{{ state.options.reasonLabel || 'Reason (optional)' }}</label>
          <Textarea id="confirm-reason" v-model="state.reason" rows="2" />
        </div>
        <div class="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <AlertDialogCancel :class="buttonVariants({ variant: 'outline' })" @click="close(false)">
            {{ state.options.cancelText || 'Cancel' }}
          </AlertDialogCancel>
          <AlertDialogAction :class="buttonVariants({ variant: state.options.destructive ? 'destructive' : 'default' })" @click="close(true)">
            {{ state.options.confirmText || 'Confirm' }}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
