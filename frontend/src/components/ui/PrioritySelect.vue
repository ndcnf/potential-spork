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
  { value: 'high', label: 'Immanquable' },
  { value: 'medium', label: 'Peut-être' },
  { value: 'ignore', label: 'Non merci' },
]

function normalizePriority(priority: Priority): SimplifiedPriority {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  if (priority === 'ignore') {
    return 'ignore'
  }

  return 'ignore'
}
</script>

<template>
  <div class="priority-select" :class="{ dense }" aria-label="Qualification du film">
    <button
      v-for="option in options"
      :key="option.value"
      class="priority-option"
      type="button"
      :class="{ active: props.modelValue !== 'unreviewed' && props.modelValue !== 'low' && normalizePriority(props.modelValue) === option.value }"
      :data-priority="option.value"
      :aria-pressed="props.modelValue !== 'unreviewed' && props.modelValue !== 'low' && normalizePriority(props.modelValue) === option.value"
      :aria-label="option.label"
      @click="$emit('update:modelValue', option.value)"
    >
      <span>{{ option.label }}</span>
    </button>
  </div>
</template>
