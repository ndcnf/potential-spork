<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { formatMinutes, formatTimeRange as formatTimeRangeValue, screeningsOverlapWithBuffer, toMinutes } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
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
  isRecommended: boolean
  recommendationNote: string | null
  recommendationReasons: string[]
}

const store = useFestivalStore()
const settingsStore = useSettingsStore()
const activeDay = ref('')
const planningMode = ref<'timeline' | 'venues'>('timeline')
const detailScreeningId = ref<number | null>(null)
const FESTIVAL_VIEW_KEY = '__festival__'

function isPlanningPriority(priority: Film['priority']): boolean {
  return priority === 'medium' || priority === 'high' || priority === 'must-see'
}

function isHighPriority(priority: Film['priority'] | undefined): boolean {
  return priority === 'high' || priority === 'must-see'
}

function screeningRecommendationScore(screening: Screening, selectedScreenings: Screening[], candidateCount: number): { score: number; note: string; reasons: string[] } {
  const settings = settingsStore.recommendationSettings
  const conflictPenalty = selectedScreenings.some((other) => screeningsOverlapWithBuffer(screening, other)) ? -100 : 0
  const rarityBonus = candidateCount === 1 ? 40 : candidateCount === 2 ? 20 : 0
  const comfortBonus = settings.preferredVenueScores[screening.venue_name ?? ''] ?? 0
  const startMinutes = toMinutes(screening.starts_at)
  const latenessPenalty = settings.avoidAfterMinutes !== null && startMinutes >= settings.avoidAfterMinutes ? -1 : 0
  const earlyPenalty = settings.avoidBeforeMinutes !== null && startMinutes < settings.avoidBeforeMinutes ? -1 : 0
  const total = conflictPenalty + rarityBonus + comfortBonus + latenessPenalty + earlyPenalty
  const reasons: string[] = []

  if (candidateCount === 1) {
    reasons.push('derniere option viable pour ce film')
  } else if (candidateCount === 2) {
    reasons.push('peu d alternatives restantes')
  }

  if (comfortBonus > 0) {
    reasons.push('salle notee plus confortable')
  }

  if (settings.avoidBeforeMinutes !== null && startMinutes < settings.avoidBeforeMinutes) {
    reasons.push('un peu avant ta plage preferee')
  }

  if (settings.avoidAfterMinutes !== null && startMinutes >= settings.avoidAfterMinutes) {
    reasons.push('un peu apres ta plage preferee')
  }

  if (conflictPenalty < 0) {
    return { score: total, note: 'conflit evite si possible', reasons: ['entre en conflit avec une seance deja choisie'] }
  }
  if (candidateCount === 1) {
    return { score: total, note: 'derniere option viable', reasons }
  }
  if (comfortBonus > 0) {
    return { score: total, note: 'salle plus confortable', reasons }
  }
  if (latenessPenalty < 0 || earlyPenalty < 0) {
    return { score: total, note: 'un peu hors preference horaire', reasons }
  }

  return { score: total, note: 'meilleur compromis actuel', reasons: reasons.length ? reasons : ['pas de conflit detecte', 'ordre chronologique favorable'] }
}

onMounted(() => {
  settingsStore.load()
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
  const validScreeningCountByFilmId = new Map<number, number>()
  const recommendationByFilmId = new Map<number, number>()
  const recommendationNoteByScreeningId = new Map<number, string>()
  const recommendationReasonsByScreeningId = new Map<number, string[]>()

  for (const screening of baseScreenings) {
    if (screening.selection_status !== 'rejected') {
      validScreeningCountByFilmId.set(screening.film_id, (validScreeningCountByFilmId.get(screening.film_id) ?? 0) + 1)
    }
  }

  const candidatesByFilmId = new Map<number, Screening[]>()
  for (const screening of baseScreenings) {
    if (screening.selection_status === 'rejected') {
      continue
    }
    candidatesByFilmId.set(screening.film_id, [...(candidatesByFilmId.get(screening.film_id) ?? []), screening])
  }

  for (const [filmId, screenings] of candidatesByFilmId.entries()) {
    const hasSelected = screenings.some((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
    if (hasSelected) {
      continue
    }

    if (settingsStore.recommendationMode === 'personalized') {
      const scored = [...screenings]
        .map((screening) => ({
          screening,
          ...screeningRecommendationScore(screening, selectedScreenings, screenings.length),
        }))
        .sort((left, right) => right.score - left.score || (left.screening.starts_at ?? '').localeCompare(right.screening.starts_at ?? ''))

      if (scored[0]) {
        recommendationByFilmId.set(filmId, scored[0].screening.id)
        recommendationNoteByScreeningId.set(scored[0].screening.id, scored[0].note)
        recommendationReasonsByScreeningId.set(scored[0].screening.id, scored[0].reasons)
      }
    }
  }

  return baseScreenings
    .map((screening) => {
      const dayKey = screening.starts_at?.slice(0, 10) ?? 'Sans date'
      const startMinutes = toMinutes(screening.starts_at)
      const endMinutes = toMinutes(screening.ends_at)
      const isSelected = screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'
      const film = filmById.value.get(screening.film_id) ?? null
      const isSingleScreening = (validScreeningCountByFilmId.get(screening.film_id) ?? 0) === 1
      const isMustLock = isSingleScreening && isHighPriority(film?.priority) && !isSelected
      const isRecommended = recommendationByFilmId.get(screening.film_id) === screening.id && !isSelected
      const recommendationNote = recommendationNoteByScreeningId.get(screening.id) ?? null
      const recommendationReasons = recommendationReasonsByScreeningId.get(screening.id) ?? []

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
        isRecommended,
        recommendationNote,
        recommendationReasons,
      }
    })
    .sort((left, right) => {
      const leftStartsAt = left.starts_at ?? ''
      const rightStartsAt = right.starts_at ?? ''
      return leftStartsAt.localeCompare(rightStartsAt) || left.film_title.localeCompare(right.film_title)
    })
})

const dayKeys = computed(() => [...new Set(planningScreenings.value.map((screening) => screening.dayKey))])
const dayOptions = computed(() => [FESTIVAL_VIEW_KEY, ...dayKeys.value])

watch(
  dayKeys,
  (days) => {
    if (!days.length) {
      activeDay.value = ''
      return
    }
    if (activeDay.value !== FESTIVAL_VIEW_KEY && !days.includes(activeDay.value)) {
      activeDay.value = days[0]
    }
  },
  { immediate: true },
)

const dayScreenings = computed(() =>
  activeDay.value === FESTIVAL_VIEW_KEY
    ? planningScreenings.value
    : planningScreenings.value.filter((screening) => screening.dayKey === activeDay.value),
)

const timelineGroups = computed(() => {
  if (activeDay.value !== FESTIVAL_VIEW_KEY) {
    return [{ dayKey: activeDay.value, screenings: dayScreenings.value }]
  }

  const grouped = new Map<string, PlanningScreening[]>()
  for (const screening of dayScreenings.value) {
    grouped.set(screening.dayKey, [...(grouped.get(screening.dayKey) ?? []), screening])
  }

  return [...grouped.entries()].map(([dayKey, screenings]) => ({
    dayKey,
    screenings,
  }))
})

const detailScreening = computed(
  () => planningScreenings.value.find((screening) => screening.id === detailScreeningId.value) ?? null,
)

const summary = computed(() => ({
  films: store.films.filter((film) => isPlanningPriority(film.priority)).length,
  selected: planningScreenings.value.filter((screening) => screening.isSelected).length,
  conflicts: planningScreenings.value.filter((screening) => screening.isSelected && screening.isConflict).length,
  toPlace: planningScreenings.value.filter((screening) => !screening.isSelected && !screening.isAlternative && screening.selection_status !== 'rejected').length,
}))

const daySummary = computed(() => ({
  total: dayScreenings.value.length,
  selected: dayScreenings.value.filter((screening) => screening.isSelected).length,
  conflicts: dayScreenings.value.filter((screening) => screening.isSelected && screening.isConflict).length,
}))

const gridVenueNames = computed(() => {
  const names = dayScreenings.value.map((screening) => screening.venue_name || 'Salle inconnue')
  return [...new Set(names)].sort((left, right) => left.localeCompare(right))
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
  if (screening.selection_status === 'rejected') return 'Ignoree'
  if (screening.isRecommended) return screening.recommendationNote ? `Recommandee · ${screening.recommendationNote}` : 'Recommandee'
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
  if (screening.selection_status === 'rejected') return 'planning__timeline-item--rejected'
  if (screening.isRecommended) return 'planning__timeline-item--recommended'
  if (screening.isAlternative || screening.derived_state === 'disabled') return 'planning__timeline-item--disabled'
  if (screening.derived_state === 'conflict') return 'planning__timeline-item--blocked'
  return 'planning__timeline-item--available'
}

function selectedCountForDay(dayKey: string): number {
  if (dayKey === FESTIVAL_VIEW_KEY) {
    return planningScreenings.value.filter((screening) => screening.isSelected).length
  }
  return planningScreenings.value.filter((screening) => screening.dayKey === dayKey && screening.isSelected).length
}

function dayChipLabel(dayKey: string): string {
  return dayKey === FESTIVAL_VIEW_KEY ? 'Festival entier' : formatDayChipLabel(dayKey)
}

function setSelection(screeningId: number, status: Screening['selection_status']): void {
  store.setScreeningSelection(screeningId, status)
}

function toggleScreeningSelection(screeningId: number, nextStatus: Screening['selection_status']): void {
  const screening = planningScreenings.value.find((item) => item.id === screeningId)
  if (!screening) {
    return
  }

  const targetStatus = screening.selection_status === nextStatus ? 'none' : nextStatus
  store.setScreeningSelection(screeningId, targetStatus)
}

function jumpToDay(dayKey: string): void {
  activeDay.value = dayKey
}

function openDetailPanel(screeningId: number): void {
  detailScreeningId.value = screeningId
}

function closeDetailPanel(): void {
  detailScreeningId.value = null
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
            <span class="legend__item"><span class="legend__marker legend__marker--recommended" /> recommandee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--conflict" /> conflit</span>
            <span class="legend__item"><span class="legend__marker legend__marker--disabled" /> autre seance deja choisie</span>
            <span class="legend__item"><span class="legend__marker legend__marker--rejected" /> seance ecartee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--available" /> disponible</span>
          </div>
        </div>
      </section>

      <section class="planning__controls-panel">
        <div class="planning__control-group planning__control-group--status">
          <p class="eyebrow">Recommandations</p>
          <p class="planning__status-note">
            <template v-if="settingsStore.recommendationMode === 'off'">Desactivees. Le planning reste manuel.</template>
            <template v-else-if="settingsStore.recommendationMode === 'neutral'">Actives, mais sans preference definie : l'app reste neutre.</template>
            <template v-else>Personnalisees selon tes parametres.</template>
          </p>
        </div>

        <div class="planning__control-group">
          <p class="eyebrow">Jour</p>
          <div class="planning__day-picker">
            <button
              v-for="day in dayOptions"
              :key="day"
              class="planning__day-button"
              :class="{ 'planning__day-button--active': activeDay === day }"
              type="button"
              @click="activeDay = day"
            >
              {{ dayChipLabel(day) }} · {{ selectedCountForDay(day) }}
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

    <section class="planning__focus-layout" :class="{ 'planning__focus-layout--with-panel': !!detailScreening }">
      <section class="planning__panel planning__panel--day">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Jour courant</p>
            <h3>{{ activeDay === FESTIVAL_VIEW_KEY ? 'Festival entier' : activeDay ? formatDayLabel(activeDay) : 'Aucun jour' }}</h3>
          </div>
          <span>{{ daySummary.selected }} choisi(es) · {{ daySummary.conflicts }} conflit(s) · {{ daySummary.total }} seance(s)</span>
        </header>

        <div v-if="planningMode === 'timeline' && dayScreenings.length" class="planning__timeline">
          <template v-for="group in timelineGroups" :key="group.dayKey || 'empty'">
            <header v-if="activeDay === FESTIVAL_VIEW_KEY" class="planning__timeline-day-header">
              <strong>{{ formatDayLabel(group.dayKey) }}</strong>
              <span>{{ group.screenings.filter((screening) => screening.isSelected).length }} retenue(s)</span>
            </header>

            <article
              v-for="screening in group.screenings"
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
                      <button type="button" class="planning__detail-trigger" @click="openDetailPanel(screening.id)">
                        {{ screening.film_title }}
                      </button>
                    </strong>
                    <span class="planning__state">{{ screeningReason(screening) }}</span>
                  </div>
                  <p>{{ screening.venue_name }}</p>
                  <p>{{ filmMeta(screening) }}</p>
                  <div class="planning__selection-toggle" role="radiogroup" aria-label="Statut de la seance">
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'tentative' }"
                      :aria-pressed="screening.selection_status === 'tentative'"
                      @click="toggleScreeningSelection(screening.id, 'tentative')"
                    >
                      Tentative
                    </button>
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'confirmed' }"
                      :aria-pressed="screening.selection_status === 'confirmed'"
                      @click="toggleScreeningSelection(screening.id, 'confirmed')"
                    >
                      Confirmee
                    </button>
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'rejected' }"
                      :aria-pressed="screening.selection_status === 'rejected'"
                      @click="toggleScreeningSelection(screening.id, 'rejected')"
                    >
                      Ignoree
                    </button>
                  </div>
                </div>
              </div>
            </article>
          </template>
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
                <strong>
                  <button type="button" class="planning__detail-trigger" @click="openDetailPanel(screening.id)">
                    {{ screening.film_title }}
                  </button>
                </strong>
                <p v-if="screening.isMustLock" class="planning__matrix-note">A securiser</p>
                <p>{{ screening.film?.tagline || 'Genre non renseigne' }}</p>
              </article>
            </div>
          </template>
        </div>

        <p v-else class="planning__empty">Aucune seance visible pour ce jour.</p>
      </section>

      <aside v-if="detailScreening" class="planning__detail-panel">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Detail film</p>
            <h3>{{ detailScreening.film_title }}</h3>
            <p v-if="detailScreening.film?.premiere_label" class="planning__detail-kicker">{{ detailScreening.film.premiere_label }}</p>
          </div>
          <button type="button" class="planning__action planning__action--ghost" @click="closeDetailPanel">Fermer</button>
        </header>

        <div v-if="detailScreening.film?.short_description" class="planning__detail-copy">
          <p>{{ detailScreening.film.short_description }}</p>
        </div>

        <div class="planning__detail-media" v-if="detailScreening.film?.poster_url">
          <img :src="detailScreening.film.poster_url" :alt="`Affiche ${detailScreening.film_title}`" />
        </div>

        <div class="planning__detail-grid">
          <div>
            <p class="planning__detail-line"><strong>Horaire</strong> {{ formatTimeRange(detailScreening) }}</p>
            <p class="planning__detail-line"><strong>Salle</strong> {{ detailScreening.venue_name || 'Salle inconnue' }}</p>
            <p class="planning__detail-line"><strong>Etat</strong> {{ screeningReason(detailScreening) }}</p>
          </div>
          <div>
            <p class="planning__detail-line"><strong>Rea</strong> {{ detailScreening.film?.directors || 'Non renseigne' }}</p>
            <p class="planning__detail-line"><strong>Infos</strong> {{ filmMeta(detailScreening) }}</p>
            <p class="planning__detail-line"><strong>Genre</strong> {{ detailScreening.film?.tagline || 'Non renseigne' }}</p>
            <p class="planning__detail-line"><strong>Langue</strong> {{ detailScreening.film?.language || 'Non renseignee' }}</p>
            <p class="planning__detail-line"><strong>Age</strong> {{ detailScreening.film?.age_rating || 'Non renseigne' }}</p>
          </div>
        </div>

        <div v-if="detailScreening.isRecommended || detailScreening.isMustLock" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Pourquoi cette seance ressort</p>
          <ul class="planning__detail-list">
            <li v-if="detailScreening.isMustLock">il ne reste qu une seule seance valable pour ce film prioritaire</li>
            <li v-for="reason in detailScreening.recommendationReasons" :key="reason">{{ reason }}</li>
          </ul>
        </div>

        <div v-if="detailScreening.film?.synopsis" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Synopsis</p>
          <p>{{ detailScreening.film.synopsis }}</p>
        </div>

        <div v-if="detailScreening.film?.cast" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Casting</p>
          <p>{{ detailScreening.film.cast }}</p>
        </div>

        <div v-if="detailScreening.film?.festival_url || detailScreening.film?.imdb_url || detailScreening.ticket_url" class="planning__links">
          <a v-if="detailScreening.film?.festival_url" :href="detailScreening.film.festival_url" target="_blank" rel="noopener">Ouvrir la fiche NIFFF</a>
          <a v-if="detailScreening.film?.imdb_url" :href="detailScreening.film.imdb_url" target="_blank" rel="noopener">IMDb</a>
          <a v-if="detailScreening.ticket_url" :href="detailScreening.ticket_url" target="_blank" rel="noopener">Billetterie</a>
        </div>
      </aside>
    </section>

  </section>
</template>
