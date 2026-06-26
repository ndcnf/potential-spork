<script setup lang="ts">
import { computed } from 'vue'

import { uiChipClasses, type UiSize, type UiTone } from './uiClasses'

const props = withDefaults(
  defineProps<{
    tone?: UiTone
    size?: UiSize
    active?: boolean
  }>(),
  {
    tone: 'neutral',
    size: 'md',
    active: false,
  },
)

const classes = computed(() => uiChipClasses({ tone: props.tone, size: props.size, active: props.active }))
</script>

<template>
  <span :class="classes">
    <span v-if="$slots.icon" class="ui-chip__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <span class="ui-chip__label">
      <slot />
    </span>
  </span>
</template>
