<script setup lang="ts">
import { computed } from 'vue'

import { uiButtonClasses, type UiButtonVariant, type UiSize, type UiTone } from './uiClasses'

const props = withDefaults(
  defineProps<{
    variant?: UiButtonVariant
    tone?: UiTone
    size?: UiSize
    active?: boolean
    block?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'ghost',
    tone: 'neutral',
    size: 'md',
    active: false,
    block: false,
    type: 'button',
  },
)

defineEmits<{
  click: [event: MouseEvent]
}>()

const classes = computed(() =>
  uiButtonClasses({
    variant: props.variant,
    tone: props.tone,
    size: props.size,
    active: props.active,
    block: props.block,
  }),
)
</script>

<template>
  <button :class="classes" :type="props.type" :aria-pressed="props.active || undefined" @click="$emit('click', $event)">
    <span v-if="$slots.icon" class="ui-button__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <span class="ui-button__label">
      <slot />
    </span>
  </button>
</template>
