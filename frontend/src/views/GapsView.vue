<script setup lang="ts">
import { onMounted } from 'vue'

import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import { useFestivalStore } from '@/stores/festival'

const store = useFestivalStore()

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Etape 3</p>
        <h2>Combler les trous</h2>
        <p class="page-copy">
          Cette vue ne doit pas polluer. On remonte surtout les films moyen, fort, immanquable qui rentrent dans les trous utiles.
        </p>
      </div>
    </header>

    <div class="gap-hero">
      <div>
        <p class="eyebrow">Trou detecte</p>
        <h3>Samedi 4 juillet · 21:15 -> 21:45</h3>
        <p>Pas assez long pour un long metrage. Rien a pousser ici.</p>
      </div>
      <div>
        <p class="eyebrow">Trou detecte</p>
        <h3>Dimanche 5 juillet · 14:00 -> 17:30</h3>
        <p>Ce trou merite une vraie suggestion, mais sans afficher les cycles ignores.</p>
      </div>
    </div>

    <section class="gap-suggestions">
      <article v-for="film in store.highlightedFilms" :key="film.id" class="gap-card">
        <div class="gap-card-main">
          <div>
            <h3>{{ film.title }}</h3>
            <p>{{ film.directors }}</p>
          </div>
          <PriorityBadge :priority="film.priority" />
        </div>
        <p>{{ film.tagline }}</p>
        <small>{{ film.duration_minutes }} min · {{ film.cycle_name }}</small>
      </article>
    </section>
  </section>
</template>
