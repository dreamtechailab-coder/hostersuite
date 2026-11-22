<script setup lang="ts">
import { ref } from 'vue'
import { FileText, Loader2, Lock, UploadCloud, X } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { uploadFile } from '@/services/api'

/**
 * Uploads to Frappe as a PRIVATE file by default (served only to permitted
 * users via /private/files and never cached by the service worker).
 */
const props = withDefaults(
  defineProps<{ doctype?: string; docname?: string; fieldname?: string; accept?: string; maxSizeMb?: number; isPrivate?: boolean; label?: string }>(),
  { accept: 'image/*,application/pdf', maxSizeMb: 5, isPrivate: true, label: 'Upload a file' },
)
const model = defineModel<string | null | undefined>()
const uploading = ref(false)
const dragging = ref(false)
const input = ref<HTMLInputElement>()

async function handle(files: FileList | null | undefined) {
  const file = files?.[0]
  if (!file) return
  if (file.size > props.maxSizeMb * 1024 * 1024) {
    toast.error(`File is larger than ${props.maxSizeMb} MB`)
    return
  }
  uploading.value = true
  try {
    const res = await uploadFile(file, { doctype: props.doctype, docname: props.docname, fieldname: props.fieldname, isPrivate: props.isPrivate })
    model.value = res.file_url
    toast.success('File uploaded')
  } catch (e) {
    toast.error((e as Error).message)
  } finally {
    uploading.value = false
    if (input.value) input.value.value = ''
  }
}
const fileName = (url: string) => decodeURIComponent(url.split('/').pop() || url)
</script>

<template>
  <div>
    <div v-if="model" class="flex items-center gap-3 rounded-lg border bg-muted/30 px-3 py-2.5">
      <FileText class="size-5 shrink-0 text-primary" />
      <a :href="model" target="_blank" rel="noopener" class="min-w-0 flex-1 truncate text-sm font-medium hover:underline">{{ fileName(model) }}</a>
      <Lock v-if="isPrivate" class="size-3.5 text-muted-foreground" aria-label="Private file" />
      <button type="button" class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground" aria-label="Remove file" @click="model = ''">
        <X class="size-4" />
      </button>
    </div>
    <label
      v-else
      :class="[
        'flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-lg border border-dashed px-4 py-6 text-center transition',
        dragging ? 'border-primary bg-primary/5' : 'hover:border-primary/50 hover:bg-muted/40',
      ]"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="(dragging = false), handle($event.dataTransfer?.files)"
    >
      <Loader2 v-if="uploading" class="size-6 animate-spin text-primary" />
      <UploadCloud v-else class="size-6 text-muted-foreground" />
      <span class="text-sm font-medium">{{ uploading ? 'Uploading…' : label }}</span>
      <span class="text-xs text-muted-foreground">PDF or image, up to {{ maxSizeMb }} MB{{ isPrivate ? ' · stored privately' : '' }}</span>
      <input ref="input" type="file" class="sr-only" :accept="accept" :disabled="uploading" @change="handle(($event.target as HTMLInputElement).files)" />
    </label>
  </div>
</template>
