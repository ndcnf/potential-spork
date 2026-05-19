<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { formatMinutes, formatTimeRange as formatTimeRangeValue, screeningsOverlapWithBuffer, toMinutes } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import type { Film, Screening } from '@/types'

type PlanningScreening = Screening & {
  film: Film | null
  dayKey: string
  startMinutes: number
  endMinutes: number
  isSelected: boolean
  isConflict: boolean
  isAlternative: boolean
  isSingleScreening: boolean
  isMustLock: boolean
}

const store = useFestivalStore()
const activeDay = ref('')
const planningMode = ref<'timeline' | 'venues'>('timeline')

function isPlanningPriority(priority: Film['priority']): boolean {
  return priority === 'medium' || priority === 'high' || priority === 'must-see'
}

function isHighPriority(priority: Film['priority'] | undefined): boolean {
  return priority === 'high' || priority === 'must-see'
}

onMounted(() => {
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

const filmById = computed(() => new Map(store.films.map((film) => [film.id, film])))

const plannableFilmIds = computed(
  () => new Set(store.films.filter((film) => isPlanningPriority(film.priority)).map((film) => film.id)),
)

const planningScreenings = computed<PlanningScreening[]>(() => {
  const baseScreenings = store.visibleScreenings.filter(
    (screening) => screening.starts_at && screening.ends_at && plannableFilmIds.value.has(screening.film_id),
  )
  const selectedScreenings = baseScreenings.filter(
    (screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed',
  )
  const selectedFilmIds = new Set(selectedScreenings.map((screening) => screening.film_id))
  const screeningCountByFilmId = new Map<number, number>()

  for (const screening of baseScreenings) {
    screeningCountByFilmId.set(screening.film_id, (screeningCountByFilmId.get(screening.film_id) ?? 0) + 1)
  }

  return baseScreenings
    .map((screening) => {
      const dayKey = screening.starts_at?.slice(0, 10) ?? 'Sans date'
      const startMinutes = toMinutes(screening.starts_at)
      const endMinutes = toMinutes(screening.ends_at)
      const isSelected = screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'
      const film = filmById.value.get(screening.film_id) ?? null
      const isSingleScreening = (screeningCountByFilmId.get(screening.film_id) ?? 0) === 1
      const isMustLock = isSingleScreening && isHighPriority(film?.priority) && !isSelected

      return {
        ...screening,
        film,
        dayKey,
        startMinutes,
        endMinutes,
        isSelected,
        isConflict: selectedScreenings.some((other) => screeningsOverlapWithBuffer(screening, other)),
        isAlternative: selectedFilmIds.has(screening.film_id) && screening.selection_status === 'none',
        isSingleScreening,
        isMustLock,
      }
    })
    .sort((left, right) => {
      const leftStartsAt = left.starts_at ?? ''
      const rightStartsAt = right.starts_at ?? ''
      return leftStartsAt.localeCompare(rightStartsAt) || left.film_title.localeCompare(right.film_title)
    })
})

const dayKeys = computed(() => [...new Set(planningScreenings.value.map((screening) => screening.dayKey))])

watch(
  dayKeys,
  (days) => {
    if (!days.length) {
      activeDay.value = ''
      return
    }
    if (!days.includes(activeDay.value)) {
      activeDay.value = days[0]
    }
  },
  { immediate: true },
)

const dayScreenings = computed(() =>
  planningScreenings.value.filter((screening) => screening.dayKey === activeDay.value),
)

const selectedFestivalScreenings = computed(() =>
  planningScreenings.value.filter((screening) => screening.isSelected),
)

const selectedFestivalByDay = computed(() => {
  const grouped = new Map<string, PlanningScreening[]>()

  for (const screening of selectedFestivalScreenings.value) {
    grouped.set(screening.dayKey, [...(grouped.get(screening.dayKey) ?? []), screening])
  }

  return [...grouped.entries()].map(([day, screenings]) => ({
    day,
    screenings: screenings.sort((left, right) => (left.starts_at ?? '').localeCompare(right.starts_at ?? '')),
  }))
})

const summary = computed(() => ({
  films: store.films.filter((film) => isPlanningPriority(film.priority)).length,
  selected: planningScreenings.value.filter((screening) => screening.isSelected).length,
  conflicts: planningScreenings.value.filter((screening) => screening.isSelected && screening.isConflict).length,
  toPlace: planningScreenings.value.filter((screening) => !screening.isSelected && !screening.isAlternative).length,
}))

const daySummary = computed(() => ({
  total: dayScreenings.value.length,
  selected: dayScreenings.value.filter((screening) => screening.isSelected).length,
  conflicts: dayScreenings.value.filter((screening) => screening.isSelected && screening.isConflict).length,
}))

const gridVenueNames = computed(() => {
  const names = dayScreenings.value.map((screening) => screening.venue_name || 'Salle inconnue')
  return [...new Set(names)]
})

const gridByVenue = computed(() =>
  gridVenueNames.value.map((venueName) => ({
    venueName,
    screenings: dayScreenings.value.filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName),
  })),
)

function formatDayLabel(dayKey: string): string {
  const date = new Date(`${dayKey}T12:00:00`)
  return new Intl.DateTimeFormat('fr-CH', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(date)
}

function formatDayChipLabel(dayKey: string): string {
  const date = new Date(`${dayKey}T12:00:00`)
  const weekday = new Intl.DateTimeFormat('fr-CH', { weekday: 'short' })
    .format(date)
    .replace('.', '')
    .toLowerCase()
  const day = new Intl.DateTimeFormat('fr-CH', { day: '2-digit' }).format(date)
  return `${weekday} ${day}`
}

function formatTimeRange(screening: PlanningScreening): string {
  return formatTimeRangeValue(screening.starts_at, screening.ends_at)
}

function filmMeta(screening: PlanningScreening): string {
  const countries = screening.film?.countries ?? 'Pays ?'
  const duration = screening.film?.duration_minutes
  return `${countries} · ${formatMinutes(duration)}`
}

function screeningReason(screening: PlanningScreening): string {
  if (screening.isSelected && screening.isConflict) return 'Conflit'
  if (screening.isMustLock) return 'A securiser'
  if (screening.selection_status === 'confirmed') return 'Confirmee'
  if (screening.selection_status === 'tentative') return 'Tentative'
  if (screening.isSingleScreening) return 'Seance unique'
  if (screening.isAlternative || screening.derived_state === 'disabled') {
    const selectedSibling = planningScreenings.value.find(
      (other) =>
        other.film_id === screening.film_id &&
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed'),
    )

    if (selectedSibling?.starts_at) {
      return `Seance prevue ${formatDayChipLabel(selectedSibling.dayKey)} a ${selectedSibling.starts_at.slice(11, 16).replace(':', 'h')}`
    }

    return 'Autre seance deja choisie'
  }
  if (screening.derived_state === 'conflict') {
    const conflictingSelected = planningScreenings.value.find(
      (other) =>
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed') &&
        screeningsOverlapWithBuffer(screening, other),
    )

    if (conflictingSelected?.starts_at) {
      return `Conflit avec ${conflictingSelected.film_title}, prevu ${formatDayChipLabel(conflictingSelected.dayKey)} a ${conflictingSelected.starts_at.slice(11, 16).replace(':', 'h')}`
    }

    return 'Conflit avec une seance deja choisie'
  }
  return 'Disponible'
}

function screeningStateClass(screening: PlanningScreening): string {
  if (screening.isSelected && screening.isConflict) return 'planning__timeline-item--conflict'
  if (screening.isMustLock) return 'planning__timeline-item--must-lock'
  if (screening.selection_status === 'confirmed') return 'planning__timeline-item--confirmed'
  if (screening.selection_status === 'tentative') return 'planning__timeline-item--tentative'
  if (screening.isAlternative || screening.derived_state === 'disabled') return 'planning__timeline-item--disabled'
  if (screening.derived_state === 'conflict') return 'planning__timeline-item--blocked'
  return 'planning__timeline-item--available'
}

function selectedCountForDay(dayKey: string): number {
  return planningScreenings.value.filter((screening) => screening.dayKey === dayKey && screening.isSelected).length
}

function setSelection(screeningId: number, status: Screening['selection_status']): void {
  store.setScreeningSelection(screeningId, status)
}

function jumpToDay(dayKey: string): void {
  activeDay.value = dayKey
}

const exportUrl = 'http://localhost:8000/api/exports/confirmed.ics'
</script>

<template>
  <section class="page planning">
    <header class="page-header">
      <div>
        <h2>Planning</h2>
        <p class="page-copy">Visualiser une journee de festival pour choisir la meilleure seance film par film.</p>
      </div>
      <a class="planning__export" :href="exportUrl" target="_blank" rel="noopener">Exporter iCal</a>
    </header>

    <section class="planning__meta-panel">
      <div class="planning__summary">
        <article class="planning__summary-card">
          <strong>{{ summary.films }}</strong>
          <span>films retenus</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.selected }}</strong>
          <span>seances choisies</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.conflicts }}</strong>
          <span>conflits reels</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.toPlace }}</strong>
          <span>seances a arbitrer</span>
        </article>
      </div>

      <section class="legend legend--planning">
        <div class="legend__group">
          <span class="legend__label">Etats</span>
          <div class="legend__items legend__items--compact">
            <span class="legend__item"><span class="legend__marker legend__marker--confirmed" /> confirmee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--tentative" /> tentative</span>
            <span class="legend__item"><span class="legend__marker legend__marker--must-lock" /> a securiser</span>
            <span class="legend__item"><span class="legend__marker legend__marker--conflict" /> conflit</span>
            <span class="legend__item"><span class="legend__marker legend__marker--disabled" /> autre seance deja choisie</span>
            <span class="legend__item"><span class="legend__marker legend__marker--available" /> disponible</span>
          </div>
        </div>
      </section>

      <section class="planning__controls-panel">
        <div class="planning__control-group">
          <p class="eyebrow">Jour</p>
          <div class="planning__day-picker">
            <button
              v-for="day in dayKeys"
              :key="day"
              class="planning__day-button"
              :class="{ 'planning__day-button--active': activeDay === day }"
              type="button"
              @click="activeDay = day"
            >
              {{ formatDayChipLabel(day) }} · {{ selectedCountForDay(day) }}
            </button>
          </div>
        </div>

        <div class="planning__control-group">
          <p class="eyebrow">Affichage</p>
          <div class="planning__mode-switch" role="tablist" aria-label="Affichage planning">
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'timeline' }" type="button" @click="planningMode = 'timeline'">
              Timeline du jour
            </button>
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'venues' }" type="button" @click="planningMode = 'venues'">
              Par salle
            </button>
          </div>
        </div>
      </section>
    </section>

    <section class="planning__panel planning__panel--day">
      <header class="planning__panel-header">
        <div>
          <p class="eyebrow">Jour courant</p>
          <h3>{{ activeDay ? formatDayLabel(activeDay) : 'Aucun jour' }}</h3>
        </div>
        <span>{{ daySummary.selected }} choisi(es) · {{ daySummary.conflicts }} conflit(s) · {{ daySummary.total }} seance(s)</span>
      </header>

      <div v-if="planningMode === 'timeline' && dayScreenings.length" class="planning__timeline">
        <article
          v-for="screening in dayScreenings"
          :key="screening.id"
          class="planning__timeline-item"
          :class="screeningStateClass(screening)"
        >
          <div class="planning__timeline-time">{{ formatTimeRange(screening) }}</div>
          <div class="planning__timeline-track">
            <div class="planning__timeline-marker" />
            <div class="planning__timeline-content">
              <div class="planning__timeline-header">
                <strong>
                  <a v-if="screening.film?.festival_url" :href="screening.film.festival_url" target="_blank" rel="noopener">
                    {{ screening.film_title }}
                  </a>
                  <template v-else>{{ screening.film_title }}</template>
                </strong>
                <span class="planning__state">{{ screeningReason(screening) }}</span>
              </div>
              <p>{{ screening.venue_name }}</p>
              <p>{{ filmMeta(screening) }}</p>
              <div v-if="screening.film?.festival_url || screening.film?.imdb_url || screening.ticket_url" class="planning__links">
                <a v-if="screening.film?.festival_url" :href="screening.film.festival_url" target="_blank" rel="noopener">Fiche NIFFF</a>
                <a v-if="screening.film?.imdb_url" :href="screening.film.imdb_url" target="_blank" rel="noopener">IMDb</a>
                <a v-if="screening.ticket_url" :href="screening.ticket_url" target="_blank" rel="noopener">Billetterie</a>
              </div>
              <div class="planning__action-group">
                <button type="button" class="planning__action planning__action--secondary" @click="setSelection(screening.id, 'tentative')">Tentative</button>
                <button type="button" class="planning__action planning__action--primary" @click="setSelection(screening.id, 'confirmed')">Confirmer</button>
                <button v-if="screening.isSelected" type="button" class="planning__action planning__action--ghost" @click="setSelection(screening.id, 'none')">Retirer</button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-else-if="planningMode === 'venues' && gridByVenue.length" class="planning__matrix">
        <div class="planning__matrix-head">Salle</div>
        <div class="planning__matrix-head">Programme</div>

        <template v-for="row in gridByVenue" :key="row.venueName">
          <div class="planning__matrix-venue">{{ row.venueName }}</div>
          <div class="planning__matrix-cell">
            <article
              v-for="screening in row.screenings"
              :key="screening.id"
              class="planning__matrix-item"
              :class="screeningStateClass(screening)"
            >
              <div class="planning__matrix-time">{{ formatTimeRange(screening) }}</div>
              <strong>{{ screening.film_title }}</strong>
              <p v-if="screening.isMustLock" class="planning__matrix-note">A securiser</p>
              <p>{{ screening.film?.tagline || 'Genre non renseigne' }}</p>
            </article>
          </div>
        </template>
      </div>

      <p v-else class="planning__empty">Aucune seance visible pour ce jour.</p>
    </section>

    <section class="planning__festival-panel">
      <header class="planning__panel-header">
        <div>
          <p class="eyebrow">Festival entier</p>
          <h3>Seances deja choisies</h3>
        </div>
        <span>{{ selectedFestivalScreenings.length }} au total</span>
      </header>

      <div v-if="selectedFestivalByDay.length" class="planning__festival-days">
        <article v-for="dayGroup in selectedFestivalByDay" :key="dayGroup.day" class="planning__festival-day">
          <header class="planning__festival-day-header">
            <strong>{{ formatDayLabel(dayGroup.day) }}</strong>
            <span>{{ dayGroup.screenings.length }} retenue(s)</span>
          </header>

          <div class="planning__festival-list">
            <article v-for="screening in dayGroup.screenings" :key="screening.id" class="planning__festival-item" :class="{ 'planning__festival-item--active': screening.dayKey === activeDay }">
              <div>
                <strong>
                  <button type="button" class="planning__jump" @click="jumpToDay(screening.dayKey)">{{ screening.film_title }}</button>
                </strong>
                <p>{{ formatTimeRange(screening) }} · {{ screening.venue_name }}</p>
              </div>
              <span class="planning__festival-state">{{ screening.selection_status === 'confirmed' ? 'Confirmee' : 'Tentative' }}</span>
            </article>
          </div>
        </article>
      </div>

      <p v-else class="planning__empty">Aucune seance choisie pour l'ensemble du festival.</p>
    </section>
  </section>
</template>
