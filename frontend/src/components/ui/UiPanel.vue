<script setup lang="ts">
import { computed } from 'vue'

import { uiPanelClasses, type UiPanelDensity } from './uiClasses'

const props = withDefaults(
  defineProps<{
    tone?: 'neutral' | 'subtle' | 'accent' | 'warning'
    density?: UiPanelDensity
  }>(),
  {
    tone: 'neutral',
    density: 'normal',
  },
)

const classes = computed(() => uiPanelClasses({ tone: props.tone, density: props.density }))
</script>

<template>
  <section :class="classes">
    <header v-if="$slots.header" class="ui-panel__header">
      <slot name="header" />
    </header>
    <div class="ui-panel__body">
      <slot />
    </div>
  </section>
</template>
