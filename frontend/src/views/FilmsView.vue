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
  return `${high} prioritaires, ${medium} intermédiaires et ${pending} restants à trier sur ${total} films visibles`
})

const hasPrioritySelection = computed(() =>
  store.films.some((film) => {
    const simplifiedPriority = normalizePriority(film.priority)
    return simplifiedPriority === 'high' || simplifiedPriority === 'medium'
  }),
)

const filtersAreActive = computed(() =>
  filters.query.trim().length > 0 || filters.priority !== 'all' || filters.hideLowNoise || filters.sort !== 'title',
)

const filmsEmptyState = computed(() => {
  if (filteredGroups.value.length > 0) {
    return null
  }

  if (filtersAreActive.value) {
    return {
      message: 'Aucun film ne correspond à vos filtres.',
      action: 'Réinitialiser les filtres',
    }
  }

  if (!hasPrioritySelection.value) {
    return {
      message: 'Commencez par qualifier quelques films pour construire votre sélection.',
      action: 'Voir tous les films',
    }
  }

  return {
    message: 'Aucun film visible pour le moment.',
    action: 'Réinitialiser les filtres',
  }
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
    return `${count} ${count > 1 ? 'séances' : 'séance'} par film`
  }

  return `${uniqueCounts[0]} à ${uniqueCounts.at(-1)} séances par film`
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
  return `${counts.pending} à traiter, ${counts.high} prioritaires, ${counts.medium} intermédiaires et ${counts.ignore} ignorés sur ${films.length} films dans ce cycle`
}

function sortPriorityForCycle(left: Film, right: Film): number {
  return priorityRank(right.priority) - priorityRank(left.priority) || left.title.localeCompare(right.title)
}

function resetFilters(): void {
  filters.query = ''
  filters.priority = 'all'
  filters.hideLowNoise = false
  filters.sort = 'title'
}
</script>

<template>
  <section class="page">
    <header class="page-header films-hero">
      <div class="films-hero__main">
        <p class="eyebrow">Étape 1 sur 2</p>
        <h2>Films</h2>
        <p class="page-copy">
          Parcours les cycles, qualifie les films, puis passe au planning quand ta sélection devient assez claire.
        </p>
      </div>

      <div class="films-progress" :aria-label="globalProgressLabel">
        <div class="films-progress__stats">
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.high }}</span>
            <span class="films-progress__label">Immanquables</span>
          </div>
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.medium }}</span>
            <span class="films-progress__label">Peut-être</span>
          </div>
          <div class="films-progress__stat">
            <span class="films-progress__value">{{ globalPriorityCounts.pending }}</span>
            <span class="films-progress__label">À traiter</span>
          </div>
        </div>

        <p class="films-progress__hint page-copy">
          {{ planningReady ? 'Ta sélection est assez claire pour commencer l\'arbitrage des séances.' : 'Commence par marquer au moins un film comme Immanquable.' }}
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
      <input v-model="filters.query" class="toolbar-input" type="search" placeholder="Rechercher un titre, un réalisateur ou un casting" />

      <select v-model="filters.priority" class="toolbar-select">
        <option value="all">Toutes les priorités</option>
        <option value="pending">À traiter</option>
        <option value="high">Immanquable</option>
        <option value="medium">Peut-être</option>
        <option value="ignore">Non merci</option>
      </select>

      <select v-model="filters.sort" class="toolbar-select">
        <option value="title">Tri alphabétique</option>
        <option value="priority">Tri par priorité</option>
        <option value="duration">Tri par durée</option>
      </select>

      <label class="toolbar-toggle">
        <input v-model="filters.hideLowNoise" type="checkbox" />
        <span>Masquer les films ignorés</span>
      </label>
    </section>

    <section class="legend">
      <div class="legend__group">
        <span class="legend__label">Cycles</span>
        <div class="legend__items">
          <span class="legend__item">chaque cycle ouvre un bloc éditorial distinct</span>
        </div>
      </div>

      <div class="legend__group">
        <span class="legend__label">Priorités</span>
        <div class="legend__items">
          <PriorityBadge priority="unreviewed" />
          <PriorityBadge priority="ignore" />
          <PriorityBadge priority="medium" />
          <PriorityBadge priority="high" />
        </div>
      </div>

      <div class="legend__group">
        <span class="legend__label">Séance</span>
        <div class="legend__items">
          <span class="film-screenings__item">ven 04.07 18h30-21h00 = séance choisie</span>
          <span class="film-screenings__item film-screenings__item--warning">pas de séance prévue = film prioritaire sans choix</span>
        </div>
      </div>
    </section>

    <section v-if="filmsEmptyState" class="empty-panel">
      <h3>Aucun film à afficher</h3>
      <p class="page-copy">{{ filmsEmptyState.message }}</p>
      <button class="ghost-button" type="button" @click="resetFilters">{{ filmsEmptyState.action }}</button>
    </section>

    <template v-else>
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
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).pending }}</strong> à traiter</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).high }}</strong> prioritaires</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).medium }}</strong> intermédiaires</span>
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
                <h4>{{ film.title }} <span class="film-title-year">({{ film.year || 'année ?' }})</span></h4>
                <PrioritySelect :model-value="film.priority" dense @update:model-value="store.updateFilmPriority(film.id, $event)" />
              </div>
              <p class="film-tagline film-tagline--inline">{{ film.tagline || 'Tagline NIFFF à importer' }}</p>
               <p class="film-meta">{{ film.directors || 'Réalisation non renseignée' }}</p>
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
               <span class="film-screenings__item film-screenings__item--warning">pas de séance prévue</span>
            </div>
          </div>
        </article>
      </div>
      </section>
    </template>

    <footer class="page-footer">
      <small>{{ store.usingMocks ? 'Données de preview : NIFFF 2025 croisé PDF + Wayback' : 'Données : base locale / API courante' }}</small>
    </footer>
  </section>
</template>
