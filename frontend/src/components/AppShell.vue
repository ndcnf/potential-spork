<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import settingsIcon from '@/assets/icons/solar--settings-bold-duotone.svg?raw'

const route = useRoute()

const tabs = [
  { label: 'Films', to: '/films', hint: 'Qualifier les envies', step: true },
  { label: 'Planning', to: '/planning', hint: 'Arbitrer les séances', step: true },
  { label: 'Paramètres', to: '/settings', hint: 'Hors flux principal', step: false },
]

const primaryTabs = computed(() => tabs.filter((tab) => tab.step))
const secondaryTabs = computed(() => tabs.filter((tab) => !tab.step))
</script>

<template>
  <div class="shell">
    <header class="app-header">
      <div class="app-header__inner content-frame">
        <div class="app-header__brand">
          <p class="eyebrow">Potential Spork</p>
          <h1>PLANIFFFICATEUR</h1>
        </div>

        <nav class="app-header__nav">
          <RouterLink
            v-for="tab in primaryTabs"
            :key="tab.to"
            :to="tab.to"
            class="app-header__link"
            :class="{ 'app-header__link--active': route.path === tab.to }"
          >
            <span>{{ tab.label }}</span>
            <small>{{ tab.hint }}</small>
          </RouterLink>
        </nav>

        <nav class="app-header__nav app-header__nav--secondary" aria-label="Navigation secondaire">
          <RouterLink
            v-for="tab in secondaryTabs"
            :key="tab.to"
            :to="tab.to"
            class="app-header__link app-header__link--secondary"
            :class="{ 'app-header__link--active': route.path === tab.to }"
          >
            <span v-if="tab.to === '/settings'" class="app-header__link-icon" aria-hidden="true" v-html="settingsIcon" />
            <span>{{ tab.label }}</span>
            <small>{{ tab.hint }}</small>
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="main-panel">
      <div class="main-panel__inner content-frame">
        <RouterView />
      </div>
    </main>

    <footer class="app-footer">
      <div class="content-frame app-footer__inner">
        <small>Icônes : Solar.</small>
      </div>
    </footer>

    <nav class="mobile-tabs">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        class="mobile-tab"
        :class="{ active: route.path === tab.to }"
      >
        <span>{{ tab.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>
