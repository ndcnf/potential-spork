<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useFestivalStore } from '@/stores/festival'

const store = useFestivalStore()

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

const groupedByDay = computed(() => {
  const map = new Map<string, typeof store.visibleScreenings>()

  for (const screening of store.visibleScreenings) {
    const key = screening.starts_at?.slice(0, 10) ?? 'Sans date'
    map.set(key, [...(map.get(key) ?? []), screening])
  }

  return [...map.entries()]
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Etape 2</p>
        <h2>Planning visuel</h2>
        <p class="page-copy">
          Une seule seance active par film. Les autres restent visibles, mais desactivees. Les conflits doivent etre evidents au premier regard.
        </p>
      </div>
    </header>

    <section class="planning-grid">
      <article v-for="[day, screenings] in groupedByDay" :key="day" class="planning-column">
        <header class="planning-column-header">
          <h3>{{ day }}</h3>
          <span>{{ screenings.length }} seance(s)</span>
        </header>

        <div v-for="screening in screenings" :key="screening.id" class="screening-card" :data-state="screening.derived_state">
          <div class="screening-head">
            <strong>{{ screening.film_title }}</strong>
            <span>{{ screening.selection_status }}</span>
          </div>
          <p>{{ screening.starts_at?.slice(11, 16) }} - {{ screening.ends_at?.slice(11, 16) }}</p>
          <p>{{ screening.venue_name || 'Salle a definir' }}</p>
        </div>
      </article>
    </section>
  </section>
</template>
