<script setup lang="ts">
import type { Priority } from '@/types'

defineProps<{ priority: Priority }>()

const labels: Record<Priority, string> = {
  ignore: 'Ignorer',
  low: 'Faible',
  medium: 'Moyen',
  high: 'Fort',
  'must-see': 'Immanquable',
}
</script>

<template>
  <span class="priority-badge" :data-priority="priority">{{ labels[priority] }}</span>
</template>
