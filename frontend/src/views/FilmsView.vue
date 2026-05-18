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
        <p class="eyebrow">Etape 1</p>
        <h2>Liste films</h2>
        <p class="page-copy">
          Vue groupee par cycle. Le cycle reste visible comme structure, mais la decision se prend au niveau du film.
        </p>
      </div>
      <div class="status-card" :class="{ mock: store.usingMocks }">
        <strong>{{ store.usingMocks ? 'Proto UI' : 'API connectee' }}</strong>
        <span>{{ store.usingMocks ? 'Donnees de demonstration' : 'Donnees du backend' }}</span>
      </div>
    </header>

    <section class="toolbar">
      <div class="toolbar-chip">Groupement par cycle</div>
      <div class="toolbar-chip">Masquer ignore / faible dans suggestions</div>
      <div class="toolbar-chip">Recherche titre / real / casting</div>
    </section>

    <section v-for="group in store.groupedFilms" :key="group.cycle.id" class="cycle-group">
      <header class="cycle-header" :style="{ borderColor: group.cycle.color ?? '#3a3a3a' }">
        <div>
          <p class="cycle-title">{{ group.cycle.name }}</p>
          <small>{{ group.films.length }} film(s)</small>
        </div>
        <PriorityBadge :priority="group.cycle.priority" />
      </header>

      <article v-for="film in group.films" :key="film.id" class="film-card">
        <div class="film-card-main">
          <div>
            <h3>{{ film.title }}</h3>
            <p class="film-meta">{{ film.directors || 'Real non renseigne' }}</p>
            <p class="film-meta">{{ film.year || 'Annee ?' }} · {{ film.countries || 'Pays ?' }} · {{ film.duration_minutes || '?' }} min</p>
          </div>
          <PriorityBadge :priority="film.priority" />
        </div>

        <p class="film-tagline">{{ film.tagline || 'Tagline NIFFF a importer' }}</p>
        <p class="film-cast">{{ film.cast || 'Casting a enrichir depuis la fiche detail' }}</p>
      </article>
    </section>
  </section>
</template>
