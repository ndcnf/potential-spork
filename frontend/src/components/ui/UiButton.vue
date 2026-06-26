<script setup lang="ts">
import { computed } from 'vue'

import { uiButtonClasses, type UiButtonVariant, type UiSize } from './uiClasses'

const props = withDefaults(
  defineProps<{
    variant?: UiButtonVariant
    size?: UiSize
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'ghost',
    size: 'md',
    type: 'button',
  },
)

defineEmits<{
  click: [event: MouseEvent]
}>()

const classes = computed(() =>
  uiButtonClasses({
    variant: props.variant,
    size: props.size,
  }),
)
</script>

<template>
  <button :class="classes" :type="props.type" @click="$emit('click', $event)">
    <span v-if="$slots.icon" class="ui-button__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <span class="ui-button__label">
      <slot />
    </span>
  </button>
</template>
