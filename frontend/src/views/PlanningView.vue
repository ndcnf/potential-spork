<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useFestivalStore } from '@/stores/festival'

const store = useFestivalStore()

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

const hourMarkers = ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00', '00:00']

const groupedByDay = computed(() => {
  const map = new Map<string, typeof store.visibleScreenings>()

  for (const screening of store.visibleScreenings) {
    const key = screening.starts_at?.slice(0, 10) ?? 'Sans date'
    map.set(key, [...(map.get(key) ?? []), screening])
  }

  return [...map.entries()].map(([day, screenings]) => ({
    day,
    screenings: [...screenings].sort((left, right) => (left.starts_at ?? '').localeCompare(right.starts_at ?? '')),
  }))
})

function startLabel(value: string | null): string {
  return value?.slice(11, 16) ?? '--:--'
}

function endLabel(value: string | null): string {
  return value?.slice(11, 16) ?? '--:--'
}

function screeningOffset(value: string | null): string {
  if (!value) return '0rem'
  const hours = Number(value.slice(11, 13))
  const minutes = Number(value.slice(14, 16))
  const normalizedHours = hours < 10 ? hours + 24 : hours
  const totalMinutes = normalizedHours * 60 + minutes
  const baseline = 10 * 60
  return `${Math.max(totalMinutes - baseline, 0) / 16}rem`
}
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

    <section class="timeline-scale">
      <span v-for="hour in hourMarkers" :key="hour">{{ hour }}</span>
    </section>

    <section class="planning-board">
      <article v-for="group in groupedByDay" :key="group.day" class="planning-day">
        <header class="planning-column-header">
          <h3>{{ group.day }}</h3>
          <span>{{ group.screenings.length }} seance(s)</span>
        </header>

        <div class="planning-track">
          <div v-for="hour in hourMarkers" :key="hour" class="planning-hour" />

          <div
            v-for="screening in group.screenings"
            :key="screening.id"
            class="screening-card screening-card--timeline"
            :data-state="screening.derived_state"
            :style="{ marginLeft: screeningOffset(screening.starts_at) }"
          >
            <div class="screening-head">
              <strong>{{ screening.film_title }}</strong>
              <span>{{ screening.selection_status }}</span>
            </div>
            <p>{{ startLabel(screening.starts_at) }} - {{ endLabel(screening.ends_at) }}</p>
            <p>{{ screening.venue_name || 'Salle a definir' }}</p>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>
