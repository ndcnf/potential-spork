<script setup lang="ts">
import { computed } from 'vue'

import {
  getScreeningStatusPresentation,
  type ScreeningStatusContext,
  type ScreeningStatusInput,
} from '@/lib/screeningStatus'

const props = withDefaults(
  defineProps<{
    screening: ScreeningStatusInput
    context?: ScreeningStatusContext
    compact?: boolean
    marker?: boolean
  }>(),
  {
    context: 'timeline',
    compact: false,
    marker: false,
  },
)

const status = computed(() => getScreeningStatusPresentation(props.screening, { context: props.context }))
const classes = computed(() => [
  props.marker ? 'planning__decision-badge' : 'planning__status-pill',
  props.compact && 'planning__decision-badge--compact',
  props.marker ? `planning__decision-badge--${status.value.tone}` : `planning__status-pill--${status.value.tone}`,
])
</script>

<template>
  <span :class="classes">
    <span v-if="props.marker" class="planning__decision-marker" aria-hidden="true" />
    {{ status.label }}
  </span>
</template>
