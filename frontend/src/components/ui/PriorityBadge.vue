<script setup lang="ts">
import type { Priority } from '@/types'

const props = defineProps<{ priority: Priority }>()

function normalizePriority(priority: Priority): 'ignore' | 'medium' | 'high' {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  return 'ignore'
}

const labels = {
  ignore: 'Ignorer',
  medium: 'Moyen',
  high: 'Prioritaire',
} as const
</script>

<template>
  <span class="priority-badge" :data-priority="normalizePriority(props.priority)">{{ labels[normalizePriority(props.priority)] }}</span>
</template>
