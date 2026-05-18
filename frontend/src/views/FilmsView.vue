<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'

import { formatTimeRange } from '@/lib/planning'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import PrioritySelect from '@/components/ui/PrioritySelect.vue'
import { useFestivalStore } from '@/stores/festival'
import type { Film, Priority, Screening } from '@/types'

const store = useFestivalStore()

const filters = reactive({
  query: '',
  priority: 'all',
  hideLowNoise: false,
  sort: 'title',
})

const openCycles = reactive<Record<number, boolean>>({})

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

const filteredGroups = computed(() => {
  const normalizedQuery = filters.query.trim().toLowerCase()

  return store.groupedFilms
    .map((group) => ({
      cycle: group.cycle,
      films: group.films
        .filter((film) => {
          if (filters.hideLowNoise && (film.priority === 'ignore' || film.priority === 'low')) {
            return false
          }

          if (filters.priority !== 'all' && film.priority !== filters.priority) {
            return false
          }

          if (!normalizedQuery) {
            return true
          }

          const haystack = [film.title, film.directors, film.countries, film.cast].filter(Boolean).join(' ').toLowerCase()
          return haystack.includes(normalizedQuery)
        })
        .sort((left, right) => sortFilms(left, right, filters.sort)),
    }))
    .filter((group) => group.films.length > 0)
})

const selectedScreeningByFilmId = computed(() => {
  const selected = new Map<number, Screening>()

  for (const screening of store.visibleScreenings) {
    if (!screening.starts_at || !screening.ends_at) {
      continue
    }

    if (screening.selection_status === 'tentative' || screening.selection_status === 'confirmed') {
      selected.set(screening.film_id, screening)
    }
  }

  return selected
})

function sortFilms(left: Film, right: Film, mode: string): number {
  if (mode === 'priority') {
    return priorityRank(right.priority) - priorityRank(left.priority) || left.title.localeCompare(right.title)
  }
  if (mode === 'duration') {
    return (left.duration_minutes ?? 999) - (right.duration_minutes ?? 999) || left.title.localeCompare(right.title)
  }
  return left.title.localeCompare(right.title)
}

function priorityRank(priority: Priority): number {
  return {
    ignore: 0,
    low: 1,
    medium: 2,
    high: 3,
    'must-see': 4,
  }[priority]
}

function isCycleOpen(cycleId: number): boolean {
  return openCycles[cycleId] ?? true
}

function toggleCycle(cycleId: number): void {
  openCycles[cycleId] = !isCycleOpen(cycleId)
}

function shouldWarnMissingScreening(priority: Priority): boolean {
  return priority === 'medium' || priority === 'high' || priority === 'must-see'
}

function formatScreeningLabel(screening: Screening): string {
  if (!screening.starts_at || !screening.ends_at) {
    return 'Horaire inconnu'
  }

  const date = new Date(`${screening.starts_at.slice(0, 10)}T12:00:00`)
  const dayLabel = new Intl.DateTimeFormat('fr-CH', { weekday: 'short' })
    .format(date)
    .replace('.', '')
    .toLowerCase()
  const day = screening.starts_at.slice(8, 10)
  const month = screening.starts_at.slice(5, 7)
  const timeRange = formatTimeRange(screening.starts_at, screening.ends_at).replace(/:/g, 'h').replace(' - ', '-')

  return `${dayLabel} ${day}.${month} ${timeRange}`
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h2>Liste films</h2>
        <p class="page-copy">
          Vue groupee par cycle. Le cycle reste visible comme structure, mais la decision se prend au niveau du film.
        </p>
      </div>
    </header>

    <section class="toolbar toolbar--filters">
      <input v-model="filters.query" class="toolbar-input" type="search" placeholder="Rechercher titre, real, casting" />

      <select v-model="filters.priority" class="toolbar-select">
        <option value="all">Toutes les priorites</option>
        <option value="must-see">Immanquable</option>
        <option value="high">Fort</option>
        <option value="medium">Moyen</option>
        <option value="low">Faible</option>
        <option value="ignore">Ignorer</option>
      </select>

      <select v-model="filters.sort" class="toolbar-select">
        <option value="title">Tri alphabetique</option>
        <option value="priority">Tri par priorite</option>
        <option value="duration">Tri par duree</option>
      </select>

      <label class="toolbar-toggle">
        <input v-model="filters.hideLowNoise" type="checkbox" />
        <span>Masquer ignore + faible</span>
      </label>
    </section>

    <section v-for="group in filteredGroups" :key="group.cycle.id" class="cycle-group">
      <header class="cycle-header" :style="{ borderColor: group.cycle.color ?? '#3a3a3a' }">
        <div class="cycle-header__main">
          <div class="cycle-header__title-row">
            <span class="cycle-header__swatch" :style="{ backgroundColor: group.cycle.color ?? '#3a3a3a' }" />
            <p class="cycle-title">{{ group.cycle.name }}</p>
          </div>
          <small class="cycle-header__meta">
            {{ group.films.length }} film(s) ·
            {{ group.films.filter((film) => film.priority === 'must-see' || film.priority === 'high').length }} fort+
          </small>
        </div>

        <div class="cycle-actions">
          <PrioritySelect :model-value="group.cycle.priority" dense @update:model-value="store.updateCyclePriority(group.cycle.id, $event)" />
          <button class="ghost-button" type="button" @click="toggleCycle(group.cycle.id)">
            {{ isCycleOpen(group.cycle.id) ? 'Replier' : 'Ouvrir' }}
          </button>
        </div>
      </header>

      <div v-if="isCycleOpen(group.cycle.id)" class="cycle-group__body">
        <article v-for="film in group.films" :key="film.id" class="film-card">
          <div class="film-card-grid">
            <div class="film-card-primary">
              <h3>{{ film.title }} <span class="film-title-year">({{ film.year || 'annee ?' }})</span></h3>
              <p class="film-meta">{{ film.directors || 'Real non renseigne' }}</p>
              <p v-if="film.cast" class="film-cast film-cast--inline">{{ film.cast }}</p>
            </div>

            <div class="film-card-side">
              <PriorityBadge :priority="film.priority" />
              <PrioritySelect :model-value="film.priority" dense @update:model-value="store.updateFilmPriority(film.id, $event)" />
            </div>

            <p class="film-meta film-meta--compact">{{ film.countries || 'Pays ?' }} · {{ film.duration_minutes || '?' }} min</p>
            <p class="film-tagline film-tagline--compact">{{ film.tagline || 'Tagline NIFFF a importer' }}</p>

            <div v-if="selectedScreeningByFilmId.get(film.id)" class="film-screenings">
              <span class="film-screenings__item">
                {{ formatScreeningLabel(selectedScreeningByFilmId.get(film.id)!) }}
              </span>
            </div>
            <div v-else-if="shouldWarnMissingScreening(film.priority)" class="film-screenings">
              <span class="film-screenings__item film-screenings__item--warning">pas de seance prevue</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <footer class="page-footer">
      <small>{{ store.usingMocks ? 'Donnees de preview : NIFFF 2025 croise PDF + Wayback' : 'Donnees : base locale / API courante' }}</small>
    </footer>
  </section>
</template>
