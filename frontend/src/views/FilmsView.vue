<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { RouterLink } from 'vue-router'

import { formatTimeRange, getFestivalDayKey } from '@/lib/planning'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import PrioritySelect from '@/components/ui/PrioritySelect.vue'
import { useFestivalStore } from '@/stores/festival'
import type { Film, Priority, Screening } from '@/types'

const store = useFestivalStore()

type PriorityFilter = 'all' | 'pending' | 'ignore' | 'medium' | 'high'

const filters = reactive({
  query: '',
  priority: 'all' as PriorityFilter,
  hideLowNoise: false,
  sort: 'title',
})

const openCycles = reactive<Record<number, boolean>>({})

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

function normalizePriority(priority: Priority): Exclude<PriorityFilter, 'all'> {
  if (priority === 'must-see' || priority === 'high') {
    return 'high'
  }

  if (priority === 'medium') {
    return 'medium'
  }

  if (priority === 'unreviewed' || priority === 'low') {
    return 'pending'
  }

  return 'ignore'
}

const filteredGroups = computed(() => {
  const normalizedQuery = filters.query.trim().toLowerCase()

  return store.groupedFilms
    .map((group) => ({
      cycle: group.cycle,
      films: group.films
        .filter((film) => {
          const simplifiedPriority = normalizePriority(film.priority)

          if (filters.hideLowNoise && simplifiedPriority === 'ignore') {
            return false
          }

          if (filters.priority !== 'all' && simplifiedPriority !== filters.priority) {
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

const screeningCountByFilmId = computed(() => {
  const counts = new Map<number, number>()

  for (const screening of store.visibleScreenings) {
    counts.set(screening.film_id, (counts.get(screening.film_id) ?? 0) + 1)
  }

  return counts
})

const visibleFilms = computed(() => filteredGroups.value.flatMap((group) => group.films))

const globalPriorityCounts = computed(() => cyclePriorityCounts(visibleFilms.value))

const planningReady = computed(() => globalPriorityCounts.value.high > 0)

const globalProgressLabel = computed(() => {
  const total = visibleFilms.value.length
  const { high, medium, pending } = globalPriorityCounts.value
  return `${high} prioritaires, ${medium} moyens et ${pending} restant a trier sur ${total} films visibles`
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
    pending: 1,
    medium: 2,
    high: 3,
  }[normalizePriority(priority)]
}

function isCycleOpen(cycleId: number): boolean {
  return openCycles[cycleId] ?? true
}

function toggleCycle(cycleId: number): void {
  openCycles[cycleId] = !isCycleOpen(cycleId)
}

function shouldWarnMissingScreening(priority: Priority): boolean {
  const simplifiedPriority = normalizePriority(priority)
  return simplifiedPriority === 'high'
}

function formatScreeningLabel(screening: Screening): string {
  if (!screening.starts_at || !screening.ends_at) {
    return 'Horaire inconnu'
  }

  const dateKey = getFestivalDayKey(screening.starts_at)
  const date = new Date(`${dateKey}T12:00:00`)
  const dayLabel = new Intl.DateTimeFormat('fr-CH', { weekday: 'short' })
    .format(date)
    .replace('.', '')
    .toLowerCase()
  const day = dateKey.slice(8, 10)
  const month = dateKey.slice(5, 7)
  const timeRange = formatTimeRange(screening.starts_at, screening.ends_at).replace(/:/g, 'h').replace(' - ', '-')

  return `${dayLabel} ${day}.${month} ${timeRange}`
}

function cycleScreeningLabel(films: Film[]): string | null {
  const counts = films
    .map((film) => screeningCountByFilmId.value.get(film.id) ?? 0)
    .filter((count) => count > 0)

  if (!counts.length) {
    return null
  }

  const uniqueCounts = [...new Set(counts)].sort((left, right) => left - right)
  if (uniqueCounts.length === 1) {
    const count = uniqueCounts[0]
    return `${count} ${count > 1 ? 'seances' : 'seance'} par film`
  }

  return `${uniqueCounts[0]} a ${uniqueCounts.at(-1)} seances par film`
}

function cyclePriorityCounts(films: Film[]): { pending: number; high: number; medium: number; ignore: number } {
  return films.reduce(
    (counts, film) => {
      const section = normalizePriority(film.priority)
      counts[section] += 1
      return counts
    },
    { pending: 0, high: 0, medium: 0, ignore: 0 },
  )
}

function cyclePriorityAccessibilityLabel(films: Film[]): string {
  const counts = cyclePriorityCounts(films)
  return `${counts.pending} a traiter, ${counts.high} prioritaires, ${counts.medium} moyens et ${counts.ignore} ignores sur ${films.length} films dans ce cycle`
}

function sortPriorityForCycle(left: Film, right: Film): number {
  return priorityRank(right.priority) - priorityRank(left.priority) || left.title.localeCompare(right.title)
}
</script>

<template>
  <section class="page">
    <header class="page-header films-hero">
      <div class="films-hero__main">
        <h2>Liste films</h2>
        <p class="page-copy">
          Vue groupee par cycle. Le cycle reste visible comme structure, mais la decision se prend au niveau du film.
        </p>
      </div>

      <div class="films-progress" :aria-label="globalProgressLabel">
        <div class="films-progress__stats">
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.high }}</span>
            <span class="films-progress__label">Prioritaires</span>
          </div>
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.medium }}</span>
            <span class="films-progress__label">Moyens</span>
          </div>
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.pending }}</span>
            <span class="films-progress__label">A traiter</span>
          </div>
        </div>

        <p class="films-progress__hint page-copy">
          {{ planningReady ? 'Vous pouvez maintenant passer au planning pour arbitrer les seances.' : 'Selectionnez au moins un film prioritaire pour lancer un arbitrage utile.' }}
        </p>

        <RouterLink
          to="/planning"
          class="films-progress__cta"
          :class="{ 'films-progress__cta--disabled': !planningReady }"
          :aria-disabled="!planningReady"
          :tabindex="planningReady ? undefined : -1"
          @click.prevent="!planningReady"
        >
          Passer au Planning
        </RouterLink>
      </div>
    </header>

    <section class="toolbar toolbar--filters">
      <input v-model="filters.query" class="toolbar-input" type="search" placeholder="Rechercher titre, real, casting" />

      <select v-model="filters.priority" class="toolbar-select">
        <option value="all">Toutes les priorites</option>
        <option value="pending">A traiter</option>
        <option value="high">Prioritaire</option>
        <option value="medium">Moyen</option>
        <option value="ignore">Ignorer</option>
      </select>

      <select v-model="filters.sort" class="toolbar-select">
        <option value="title">Tri alphabetique</option>
        <option value="priority">Tri par priorite</option>
        <option value="duration">Tri par duree</option>
      </select>

      <label class="toolbar-toggle">
        <input v-model="filters.hideLowNoise" type="checkbox" />
        <span>Masquer les films ignores</span>
      </label>
    </section>

    <section class="legend">
      <div class="legend__group">
        <span class="legend__label">Cycles</span>
        <div class="legend__items">
          <span class="legend__item">chaque cycle ouvre un bloc editorial distinct</span>
        </div>
      </div>

      <div class="legend__group">
        <span class="legend__label">Priorites</span>
        <div class="legend__items">
          <PriorityBadge priority="unreviewed" />
          <PriorityBadge priority="ignore" />
          <PriorityBadge priority="medium" />
          <PriorityBadge priority="high" />
        </div>
      </div>

      <div class="legend__group">
        <span class="legend__label">Seance</span>
        <div class="legend__items">
          <span class="film-screenings__item">ven 04.07 18h30-21h00 = seance choisie</span>
          <span class="film-screenings__item film-screenings__item--warning">pas de seance prevue = film prioritaire sans choix</span>
        </div>
      </div>
    </section>

    <section v-for="group in filteredGroups" :key="group.cycle.id" class="cycle-group">
      <header class="cycle-header">
        <div class="cycle-header__main">
          <div class="cycle-header__title-row">
            <span class="cycle-header__eyebrow">Cycle</span>
            <p class="cycle-title"><span class="cycle-title__ink">{{ group.cycle.name }}</span></p>
          </div>
          <small class="cycle-header__meta">
            <template v-if="cycleScreeningLabel(group.films)">
              <span>{{ cycleScreeningLabel(group.films) }}</span>
              <span class="cycle-header__separator" aria-hidden="true">·</span>
            </template>
            <span class="cycle-header__priority-dots" :aria-label="cyclePriorityAccessibilityLabel(group.films)" role="img">
              <span
                v-for="film in [...group.films].sort(sortPriorityForCycle)"
                :key="film.id"
                class="cycle-header__priority-dot"
                :data-priority="normalizePriority(film.priority)"
              />
            </span>
            <span class="cycle-header__separator" aria-hidden="true">·</span>
            <span class="cycle-header__counters">
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).pending }}</strong> a traiter</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).high }}</strong> prioritaires</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).medium }}</strong> moyens</span>
            </span>
          </small>
        </div>

        <div class="cycle-actions">
          <button class="ghost-button" type="button" @click="toggleCycle(group.cycle.id)">
            {{ isCycleOpen(group.cycle.id) ? 'Replier' : 'Ouvrir' }}
          </button>
        </div>
      </header>

      <div v-if="isCycleOpen(group.cycle.id)" class="cycle-group__body">
        <article v-for="film in group.films" :key="film.id" class="film-card" :data-priority="normalizePriority(film.priority)">
          <div class="film-card-stack">
            <div class="film-card-primary">
              <div class="film-card-heading">
                <h4>{{ film.title }} <span class="film-title-year">({{ film.year || 'annee ?' }})</span></h4>
                <PrioritySelect :model-value="film.priority" dense @update:model-value="store.updateFilmPriority(film.id, $event)" />
              </div>
              <p class="film-tagline film-tagline--inline">{{ film.tagline || 'Tagline NIFFF a importer' }}</p>
              <p class="film-meta">{{ film.directors || 'Real non renseigne' }}</p>
              <p v-if="film.cast" class="film-cast film-cast--inline">{{ film.cast }}</p>
              <p class="film-meta film-meta--compact">
                {{ film.countries || 'Pays ?' }} · {{ film.duration_minutes || '?' }} min · {{ film.cycle_name || group.cycle.name }}
              </p>
            </div>

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
