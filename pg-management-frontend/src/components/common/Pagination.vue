<script setup lang="ts">
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const props = defineProps<{ page: number; pageCount: number; total: number; from: number; to: number }>()
const emit = defineEmits<{ 'update:page': [p: number] }>()
</script>

<template>
  <div v-if="total > 0" class="flex items-center justify-between gap-3 border-t px-4 py-3 text-sm">
    <p class="text-muted-foreground">
      <span class="tabular font-medium text-foreground">{{ from }}–{{ to }}</span> of <span class="tabular">{{ total }}</span>
    </p>
    <div class="flex items-center gap-1">
      <Button variant="outline" size="icon-sm" class="size-10 sm:size-8" :disabled="props.page <= 1" aria-label="Previous page" @click="emit('update:page', props.page - 1)">
        <ChevronLeft />
      </Button>
      <span class="tabular px-2 text-muted-foreground">{{ page }} / {{ pageCount }}</span>
      <Button variant="outline" size="icon-sm" class="size-10 sm:size-8" :disabled="props.page >= pageCount" aria-label="Next page" @click="emit('update:page', props.page + 1)">
        <ChevronRight />
      </Button>
    </div>
  </div>
</template>
