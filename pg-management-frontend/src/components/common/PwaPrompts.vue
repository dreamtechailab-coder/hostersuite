<script setup lang="ts">
import { watch } from 'vue'
import { toast } from 'vue-sonner'
import { WifiOff } from 'lucide-vue-next'
import { usePwaUpdate } from '@/composables/usePwa'
import { useOnline } from '@/composables/useOnline'

const { needRefresh, offlineReady, update } = usePwaUpdate()
const online = useOnline()

watch(needRefresh, (v) => {
  if (v)
    toast('A new version is available', {
      description: 'Reload to get the latest features and fixes.',
      duration: Infinity,
      action: { label: 'Reload', onClick: () => update() },
    })
})
watch(offlineReady, (v) => v && toast.success('App ready to install and open quickly, even on slow networks'))
</script>

<template>
  <Transition enter-from-class="-translate-y-full" leave-to-class="-translate-y-full" enter-active-class="transition" leave-active-class="transition">
    <div v-if="!online" role="status" class="fixed inset-x-0 top-0 z-[60] flex items-center justify-center gap-2 bg-warning px-4 py-1.5 text-center text-xs font-medium text-white" style="padding-top: max(0.375rem, env(safe-area-inset-top))">
      <WifiOff class="size-3.5" />
      You're offline – showing the app shell only. Changes and payments can't be saved until you reconnect.
    </div>
  </Transition>
</template>
