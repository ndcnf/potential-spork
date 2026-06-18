<script setup lang="ts">
import { normalizePriority, priorityLabels } from '@/lib/priorities'
import type { Priority } from '@/types'

const props = defineProps<{ priority: Priority }>()
</script>

<template>
  <span class="priority-badge" :data-priority="normalizePriority(props.priority)">{{ priorityLabels[normalizePriority(props.priority)] }}</span>
</template>
