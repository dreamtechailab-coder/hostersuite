<script setup lang="ts">
import { computed, useId } from 'vue'
import { Label } from '@/components/ui/label'

const props = defineProps<{ label?: string; error?: string; hint?: string; required?: boolean; id?: string; class?: string }>()
const autoId = useId()
const fieldId = computed(() => props.id || `f-${autoId}`)
</script>

<template>
  <div :class="['flex flex-col gap-1.5', props.class]">
    <Label v-if="label" :for="fieldId" class="text-[13px]">
      {{ label }}<span v-if="required" class="text-destructive" aria-hidden="true">*</span>
    </Label>
    <slot :id="fieldId" :invalid="!!error" :describedby="error ? `${fieldId}-err` : hint ? `${fieldId}-hint` : undefined" />
    <p v-if="error" :id="`${fieldId}-err`" class="text-xs font-medium text-destructive" role="alert">{{ error }}</p>
    <p v-else-if="hint" :id="`${fieldId}-hint`" class="text-xs text-muted-foreground">{{ hint }}</p>
  </div>
</template>
