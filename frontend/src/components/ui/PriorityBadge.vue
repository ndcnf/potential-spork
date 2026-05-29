<script setup lang="ts">
import type { Priority } from '@/types'

const props = defineProps<{ priority: Priority }>()

function normalizePriority(priority: Priority): 'pending' | 'ignore' | 'medium' | 'high' {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  if (priority === 'unreviewed' || priority === 'low') {
    return 'pending'
  }

  return 'ignore'
}

const labels = {
  pending: 'A traiter',
  ignore: 'Non merci',
  medium: 'Peut-etre',
  high: 'Immanquable',
} as const
</script>

<template>
  <span class="priority-badge" :data-priority="normalizePriority(props.priority)">{{ labels[normalizePriority(props.priority)] }}</span>
</template>
