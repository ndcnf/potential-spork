<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { label: 'Films', to: '/films', hint: 'Selection initiale' },
  { label: 'Planning', to: '/planning', hint: 'Assemblage visuel' },
  { label: 'Trous', to: '/gaps', hint: 'Remplissage cible' },
]
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Potential Spork</p>
        <h1>Festival planner</h1>
        <p class="sidebar-copy">
          Prioriser les films d'abord, visualiser les seances ensuite, combler les trous sans bruit.
        </p>
      </div>

      <nav class="nav">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.to"
          :to="tab.to"
          class="nav-link"
          :class="{ active: route.path === tab.to }"
        >
          <span>{{ tab.label }}</span>
          <small>{{ tab.hint }}</small>
        </RouterLink>
      </nav>

      <div class="sidebar-card">
        <strong>V1</strong>
        <p>Mono-festival, priorites cycle/film, planning manuel assiste, export `.ics`.</p>
      </div>
    </aside>

    <main class="main-panel">
      <RouterView />
    </main>
  </div>
</template>
