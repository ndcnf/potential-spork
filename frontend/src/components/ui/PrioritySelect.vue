<script setup lang="ts">
import type { Priority } from '@/types'

const props = defineProps<{
  modelValue: Priority
  dense?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: Priority]
}>()

type SimplifiedPriority = 'ignore' | 'medium' | 'high'

const options: Array<{ value: SimplifiedPriority; label: string }> = [
  { value: 'ignore', label: 'Ignorer' },
  { value: 'medium', label: 'Moyen' },
  { value: 'high', label: 'Prioritaire' },
]

const shortLabels: Record<SimplifiedPriority, string> = {
  ignore: 'I',
  medium: 'M',
  high: 'P',
}

function normalizePriority(priority: Priority): SimplifiedPriority {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  return 'ignore'
}
</script>

<template>
  <div class="priority-select" :class="{ dense }" role="radiogroup" aria-label="Priorite">
    <button
      v-for="option in options"
      :key="option.value"
      class="priority-option"
      type="button"
      :class="{ active: normalizePriority(props.modelValue) === option.value }"
      :data-priority="option.value"
      :aria-pressed="normalizePriority(props.modelValue) === option.value"
      @click="$emit('update:modelValue', option.value)"
    >
      <span v-if="dense">{{ shortLabels[option.value] }}</span>
      <span v-else>{{ option.label }}</span>
    </button>
  </div>
</template>
