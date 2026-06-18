<script setup lang="ts">
import { isPrioritySelected, normalizePriority, priorityOptions as options } from '@/lib/priorities'
import type { Priority } from '@/types'

const props = defineProps<{
  modelValue: Priority
  dense?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: Priority]
}>()
</script>

<template>
  <div class="priority-select" :class="{ dense }" aria-label="Qualification du film">
    <button
      v-for="option in options"
      :key="option.value"
      class="priority-option"
      type="button"
      :class="{ active: isPrioritySelected(props.modelValue) && normalizePriority(props.modelValue) === option.value }"
      :data-priority="option.value"
      :aria-pressed="isPrioritySelected(props.modelValue) && normalizePriority(props.modelValue) === option.value"
      :aria-label="option.label"
      @click="$emit('update:modelValue', option.value)"
    >
      <span>{{ option.label }}</span>
    </button>
  </div>
</template>
