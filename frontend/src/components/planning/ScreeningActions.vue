<script setup lang="ts">
import { computed } from 'vue'

import UiButton from '@/components/ui/UiButton.vue'
import {
  getScreeningActions,
  type ScreeningActionContext,
  type ScreeningActionScreening,
  type ScreeningActionSelectionStatus,
} from '@/lib/screeningActions'
import type { UiSize } from '@/components/ui/uiClasses'

const props = withDefaults(
  defineProps<{
    screening: ScreeningActionScreening
    context?: ScreeningActionContext
    size?: UiSize
  }>(),
  {
    context: 'detail',
    size: 'md',
  },
)

const emit = defineEmits<{
  select: [status: ScreeningActionSelectionStatus]
  clear: []
}>()

const actions = computed(() => getScreeningActions(props.screening, { context: props.context }))

function applyAction(action: (typeof actions.value)[number]) {
  if (action.kind === 'select') {
    emit('select', action.status)
    return
  }

  if (action.kind === 'clear') {
    emit('clear')
  }
}
</script>

<template>
  <div class="screening-actions" aria-label="Actions sur la séance">
    <UiButton
      v-for="action in actions"
      :key="`${action.kind}-${action.label}`"
      :variant="action.variant"
      :size="props.size"
      :disabled="action.kind === 'state'"
      @click="applyAction(action)"
    >
      {{ action.label }}
    </UiButton>
  </div>
</template>
