<script setup lang="ts">
import { useIcalExport } from '@/composables/useIcalExport'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const { exportHref, exportIcal } = useIcalExport()

const tabs = [
  { label: '1. Films', to: '/films', hint: 'Selection editoriale', step: true },
  { label: '2. Planning', to: '/planning', hint: 'Arbitrer les conflits', step: true },
  { label: 'Parametres', to: '/settings', hint: 'Hors parcours principal', step: false },
]
</script>

<template>
  <div class="shell">
    <header class="app-header">
      <div class="app-header__inner">
        <div class="app-header__brand">
          <p class="eyebrow">Potential Spork</p>
          <h1>Festival planner</h1>
        </div>

        <nav class="app-header__nav">
          <RouterLink
            v-for="tab in tabs"
            :key="tab.to"
            :to="tab.to"
            class="app-header__link"
            :class="{ 'app-header__link--active': route.path === tab.to, 'app-header__link--secondary': !tab.step }"
          >
            <span>{{ tab.label }}</span>
            <small>{{ tab.hint }}</small>
          </RouterLink>
        </nav>

        <div class="app-header__actions">
          <a class="app-header__export" :href="exportHref" target="_blank" rel="noopener" @click="exportIcal">Exporter iCal</a>
        </div>
      </div>
    </header>

    <main class="main-panel">
      <div class="main-panel__inner">
        <RouterView />
      </div>
    </main>

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
