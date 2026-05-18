<script setup lang="ts">
import type { Priority } from '@/types'

defineProps<{
  modelValue: Priority
  dense?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: Priority]
}>()

const options: Array<{ value: Priority; label: string }> = [
  { value: 'ignore', label: 'Ignorer' },
  { value: 'low', label: 'Faible' },
  { value: 'medium', label: 'Moyen' },
  { value: 'high', label: 'Fort' },
  { value: 'must-see', label: 'Immanquable' },
]

const shortLabels: Record<Priority, string> = {
  ignore: 'I',
  low: 'F',
  medium: 'M',
  high: 'H',
  'must-see': '!',
}
</script>

<template>
  <div class="priority-select" :class="{ dense }" role="radiogroup" aria-label="Priorite">
    <button
      v-for="option in options"
      :key="option.value"
      class="priority-option"
      type="button"
      :class="{ active: modelValue === option.value }"
      :data-priority="option.value"
      :aria-pressed="modelValue === option.value"
      @click="$emit('update:modelValue', option.value)"
    >
      <span v-if="dense">{{ shortLabels[option.value] }}</span>
      <span v-else>{{ option.label }}</span>
    </button>
  </div>
</template>
