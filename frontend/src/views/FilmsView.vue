<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { formatTimeRange, getFestivalDayKey } from '@/lib/planning'
import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import PrioritySelect from '@/components/ui/PrioritySelect.vue'
import { useFestivalStore } from '@/stores/festival'
import type { Film, Priority, Screening } from '@/types'

const store = useFestivalStore()

type PriorityFilter = 'all' | 'pending' | 'ignore' | 'medium' | 'high'

const activePriorityFilters = ref<Array<Exclude<PriorityFilter, 'all'>>>([])

const transitionFeedback = reactive<{ message: string; tone: 'success' | 'info'; visible: boolean; timer: ReturnType<typeof setTimeout> | null }>({
  message: '',
  tone: 'success',
  visible: false,
  timer: null,
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
  const priorityFilters = new Set(activePriorityFilters.value)

  return store.groupedFilms
    .map((group) => ({
      cycle: group.cycle,
      films: group.films
        .filter((film) => {
          const simplifiedPriority = normalizePriority(film.priority)

          if (!priorityFilters.size) {
            return true
          }

          return priorityFilters.has(simplifiedPriority)
        })
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

const allFilms = computed(() => store.groupedFilms.flatMap((group) => group.films))

const globalPriorityCounts = computed(() => cyclePriorityCounts(allFilms.value))

const initialLoading = computed(() => store.loading && !store.cycles.length && !store.films.length)

const globalProgressLabel = computed(() => {
  const total = allFilms.value.length
  const { high, medium, pending, ignore } = globalPriorityCounts.value
  return `${pending} à traiter, ${high} immanquables, ${medium} peut-être et ${ignore} non merci sur ${total} films`
})

const hasPrioritySelection = computed(() =>
  store.films.some((film) => {
    const simplifiedPriority = normalizePriority(film.priority)
    return simplifiedPriority === 'high' || simplifiedPriority === 'medium'
  }),
)

const filtersAreActive = computed(() => activePriorityFilters.value.length > 0)

const filmsEmptyState = computed(() => {
  if (filteredGroups.value.length > 0) {
    return null
  }

  if (filtersAreActive.value) {
    return {
      message: 'Aucun film ne correspond à tes filtres.',
      action: 'Réinitialiser les filtres',
    }
  }

  if (!hasPrioritySelection.value) {
    return {
      message: 'Commence par qualifier quelques films pour construire ta sélection.',
      action: 'Voir tous les films',
    }
  }

  return {
    message: 'Aucun film visible pour le moment.',
    action: 'Réinitialiser les filtres',
  }
})

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
  return `${counts.pending} à traiter, ${counts.high} immanquables, ${counts.medium} peut-être et ${counts.ignore} non merci sur ${films.length} films dans ce cycle`
}

function sortPriorityForCycle(left: Film, right: Film): number {
  return priorityRank(right.priority) - priorityRank(left.priority) || left.title.localeCompare(right.title)
}

function resetFilters(): void {
  activePriorityFilters.value = []
}

function togglePriorityFilter(priority: Exclude<PriorityFilter, 'all'>): void {
  activePriorityFilters.value = activePriorityFilters.value.includes(priority)
    ? activePriorityFilters.value.filter((entry) => entry !== priority)
    : [...activePriorityFilters.value, priority]
}

function priorityFilterButtonLabel(priority: Exclude<PriorityFilter, 'all'>): string {
  const labels = {
    pending: 'À traiter',
    high: 'Immanquables',
    medium: 'Peut-être',
    ignore: 'Non merci',
  } as const

  return labels[priority]
}

function showTransitionFeedback(message: string, tone: 'success' | 'info' = 'success') {
  if (transitionFeedback.timer) {
    clearTimeout(transitionFeedback.timer)
  }

  transitionFeedback.message = message
  transitionFeedback.tone = tone
  transitionFeedback.visible = true
  transitionFeedback.timer = setTimeout(() => {
    transitionFeedback.visible = false
    transitionFeedback.timer = null
  }, 2600)
}

function priorityLabel(priority: Priority): string {
  const simplified = normalizePriority(priority)

  if (simplified === 'high') return 'Immanquable'
  if (simplified === 'medium') return 'Peut-être'
  if (simplified === 'ignore') return 'Non merci'
  return 'À traiter'
}

function applyFilmPriority(film: Film, priority: Priority) {
  store.updateFilmPriority(film.id, priority)
  showTransitionFeedback(`${film.title} passe en ${priorityLabel(priority)}.`)
}
</script>

<template>
  <section class="page">
    <section v-if="initialLoading" class="page" aria-label="Chargement des films">
      <header class="page-header films-hero">
        <div class="films-hero__main skeleton-block">
          <span class="skeleton-line skeleton-line--xs" />
          <span class="skeleton-line skeleton-line--md" />
          <span class="skeleton-line skeleton-line--lg" />
        </div>
        <div class="films-progress skeleton-block">
          <div class="films-progress__stats">
            <span class="skeleton-chip" />
            <span class="skeleton-chip" />
            <span class="skeleton-chip" />
          </div>
          <span class="skeleton-line skeleton-line--lg" />
        </div>
      </header>

      <section class="cycle-group skeleton-block">
        <span class="skeleton-line skeleton-line--sm" />
        <span class="skeleton-line skeleton-line--md" />
        <div class="skeleton-list">
          <span class="skeleton-card" />
          <span class="skeleton-card" />
          <span class="skeleton-card" />
          <span class="skeleton-card" />
        </div>
      </section>
    </section>

    <template v-else>
    <section
      v-if="transitionFeedback.visible"
      class="notice-panel notice-panel--toast"
      :class="transitionFeedback.tone === 'success' ? 'notice-panel--success' : 'notice-panel--info'"
    >
      <p class="page-copy">{{ transitionFeedback.message }}</p>
    </section>

    <header class="page-header films-hero">
      <div class="films-hero__main">
        <h2>Films</h2>
        <p class="page-copy">
          Parcours les cycles et qualifie les films selon ce qui mérite vraiment ton attention.
        </p>
      </div>

      <div class="films-progress" :aria-label="globalProgressLabel">
        <div class="films-progress__stats">
          <button
            type="button"
            class="films-progress__stat"
            data-priority-filter="pending"
            :class="{ 'films-progress__stat--active': activePriorityFilters.includes('pending') }"
            @click="togglePriorityFilter('pending')"
          >
            <span class="films-progress__value">{{ globalPriorityCounts.pending }}</span>
            <span class="films-progress__label">À traiter</span>
          </button>
          <button
            type="button"
            class="films-progress__stat"
            data-priority-filter="high"
            :class="{ 'films-progress__stat--active': activePriorityFilters.includes('high') }"
            @click="togglePriorityFilter('high')"
          >
            <span class="films-progress__value">{{ globalPriorityCounts.high }}</span>
            <span class="films-progress__label">Immanquables</span>
          </button>
          <button
            type="button"
            class="films-progress__stat"
            data-priority-filter="medium"
            :class="{ 'films-progress__stat--active': activePriorityFilters.includes('medium') }"
            @click="togglePriorityFilter('medium')"
          >
            <span class="films-progress__value">{{ globalPriorityCounts.medium }}</span>
            <span class="films-progress__label">Peut-être</span>
          </button>
          <button
            type="button"
            class="films-progress__stat films-progress__stat--muted"
            data-priority-filter="ignore"
            :class="{ 'films-progress__stat--active': activePriorityFilters.includes('ignore') }"
            @click="togglePriorityFilter('ignore')"
          >
            <span class="films-progress__value">{{ globalPriorityCounts.ignore }}</span>
            <span class="films-progress__label">Non merci</span>
          </button>
        </div>
      </div>
    </header>

    <section v-if="store.loadError" class="notice-panel notice-panel--warning">
      <h3>Mode démo</h3>
      <p class="page-copy">{{ store.loadError }}</p>
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
          <span class="film-screenings__item film-screenings__item--warning">pas de séance prévue = film immanquable sans choix</span>
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
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).high }}</strong> immanquables</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).medium }}</strong> peut-être</span>
              <span class="cycle-header__counter"><strong>{{ cyclePriorityCounts(group.films).ignore }}</strong> non merci</span>
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
            <div class="film-card-heading">
              <h4>{{ film.title }} <span class="film-title-year">({{ film.year || 'année ?' }})</span></h4>
            </div>

            <PrioritySelect class="film-card-control" :model-value="film.priority" dense @update:model-value="applyFilmPriority(film, $event)" />

            <div class="film-card-copy">
              <p class="film-tagline film-tagline--inline">{{ film.tagline || 'Tagline NIFFF à importer' }}</p>
              <p class="film-meta">{{ film.directors || 'Réalisation non renseignée' }}</p>
              <p v-if="film.cast" class="film-cast film-cast--inline">{{ film.cast }}</p>
              <p class="film-meta film-meta--compact">
                {{ film.countries || 'Pays ?' }} · {{ film.duration_minutes || '?' }} min · {{ film.cycle_name || group.cycle.name }}
              </p>
            </div>

            <div v-if="selectedScreeningByFilmId.get(film.id)" class="film-screenings film-screenings--slot">
              <span class="film-screenings__item">
                {{ formatScreeningLabel(selectedScreeningByFilmId.get(film.id)!) }}
              </span>
            </div>
            <div v-else-if="shouldWarnMissingScreening(film.priority)" class="film-screenings film-screenings--slot">
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
    </template>
  </section>
</template>
