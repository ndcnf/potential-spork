<script setup lang="ts">
import { computed } from 'vue'

import { uiBadgeClasses, type UiSize, type UiTone } from './uiClasses'

const props = withDefaults(
  defineProps<{
    tone?: UiTone
    size?: UiSize
  }>(),
  {
    tone: 'neutral',
    size: 'md',
  },
)

const classes = computed(() => uiBadgeClasses({ tone: props.tone, size: props.size }))
</script>

<template>
  <span :class="classes">
    <span v-if="$slots.marker" class="ui-badge__marker" aria-hidden="true">
      <slot name="marker" />
    </span>
    <span class="ui-badge__label">
      <slot />
    </span>
  </span>
</template>
