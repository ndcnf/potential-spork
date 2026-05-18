<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { formatMinutes, formatTimeRange as formatTimeRangeValue, RESERVATION_BUFFER_MINUTES, screeningsOverlapWithBuffer, toMinutes } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import type { Film, Screening } from '@/types'

type PlanningGap = {
  dayKey: string
  start: string
  end: string
  durationMinutes: number
}

type PlanningScreening = Screening & {
  film: Film | null
  dayKey: string
  startMinutes: number
  endMinutes: number
  isSelected: boolean
  isAlternative: boolean
  isConflict: boolean
}

const store = useFestivalStore()
const activeDay = ref('')
const planningMode = ref<'plan' | 'grid'>('plan')

function isPlanningPriority(priority: Film['priority']): boolean {
  return priority === 'medium' || priority === 'high' || priority === 'must-see'
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
  const baseScreenings = store.visibleScreenings.filter((screening) => screening.starts_at && screening.ends_at)
  const selectedScreenings = baseScreenings.filter(
    (screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed',
  )
  const selectedFilmIds = new Set(selectedScreenings.map((screening) => screening.film_id))

  return baseScreenings
    .filter((screening) => screening.starts_at && screening.ends_at)
    .filter((screening) => plannableFilmIds.value.has(screening.film_id))
    .map((screening) => {
      const dayKey = screening.starts_at?.slice(0, 10) ?? 'Sans date'
      const startMinutes = toMinutes(screening.starts_at)
      const endMinutes = toMinutes(screening.ends_at)
      const isSelected = screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'
      const isConflict = selectedScreenings.some((other) => screeningsOverlapWithBuffer(screening, other))

      return {
        ...screening,
        film: filmById.value.get(screening.film_id) ?? null,
        dayKey,
        startMinutes,
        endMinutes,
        isSelected,
        isAlternative: selectedFilmIds.has(screening.film_id) && screening.selection_status === 'none',
        isConflict,
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

const selectedDayScreenings = computed(() => planningScreenings.value.filter((screening) => screening.dayKey === activeDay.value))

const selectedAgenda = computed(() => selectedDayScreenings.value.filter((screening) => screening.isSelected))

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

const candidateList = computed(() =>
  selectedDayScreenings.value.filter(
    (screening) =>
      !screening.isSelected &&
      screening.derived_state !== 'disabled' &&
      screening.derived_state !== 'past' &&
      screening.derived_state !== 'conflict',
  ),
)

const conflictList = computed(() =>
  selectedDayScreenings.value.filter((screening) => screening.isSelected && screening.isConflict),
)

const alternativesList = computed(() =>
  selectedDayScreenings.value.filter((screening) => screening.isAlternative || screening.derived_state === 'disabled'),
)

const dayGaps = computed<PlanningGap[]>(() => {
  const selected = [...selectedAgenda.value].sort((left, right) => left.startMinutes - right.startMinutes)
  const gaps: PlanningGap[] = []

  for (let index = 0; index < selected.length - 1; index += 1) {
    const current = selected[index]
    const next = selected[index + 1]
    const duration = next.startMinutes - current.endMinutes

    if (duration >= RESERVATION_BUFFER_MINUTES) {
      gaps.push({
        dayKey: current.dayKey,
        start: current.ends_at?.slice(11, 16) ?? '--:--',
        end: next.starts_at?.slice(11, 16) ?? '--:--',
        durationMinutes: duration,
      })
    }
  }

  return gaps
})

const summary = computed(() => ({
  films: store.films.filter((film) => isPlanningPriority(film.priority)).length,
  selected: planningScreenings.value.filter((screening) => screening.isSelected).length,
  conflicts: planningScreenings.value.filter((screening) => screening.isSelected && screening.isConflict).length,
  alternatives: planningScreenings.value.filter((screening) => screening.isAlternative || screening.derived_state === 'disabled').length,
  gaps: dayGaps.value.length,
}))

const gridVenueNames = computed(() => {
  const names = selectedDayScreenings.value.map((screening) => screening.venue_name || 'Salle inconnue')
  return [...new Set(names)]
})

const gridByVenue = computed(() =>
  gridVenueNames.value.map((venueName) => ({
    venueName,
    screenings: selectedDayScreenings.value.filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName),
  })),
)

function formatDayLabel(dayKey: string): string {
  const date = new Date(`${dayKey}T12:00:00`)
  return new Intl.DateTimeFormat('fr-CH', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(date)
}

function selectedCountForDay(dayKey: string): number {
  return planningScreenings.value.filter((screening) => screening.dayKey === dayKey && screening.isSelected).length
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
  if (screening.isConflict) return 'Conflit avec autre seance choisie'
  if (screening.selection_status === 'confirmed') return 'Confirmee'
  if (screening.selection_status === 'tentative') return 'Tentative'
  if (screening.derived_state === 'disabled') return 'Autre seance de ce film deja choisie'
  if (screening.derived_state === 'conflict') return 'Chevauche une seance deja choisie'
  return 'Disponible'
}

function gapLabel(durationMinutes: number): string {
  if (durationMinutes <= 15) return 'Faudra courir'
  if (durationMinutes <= 45) return 'Tu peux souffler un peu'
  if (durationMinutes <= 120) return "T'as pense a manger ?"
  return "C'est un jour de conge ?"
}

function setSelection(screeningId: number, status: Screening['selection_status']): void {
  store.setScreeningSelection(screeningId, status)
}

const exportUrl = 'http://localhost:8000/api/exports/confirmed.ics'
</script>

<template>
  <section class="page planning">
    <header class="page-header">
      <div>
        <p class="eyebrow">Etape 2</p>
        <h2>Planning visuel</h2>
        <p class="page-copy">
          Une vue pour arbitrer le plan choisi, une vue pour retrouver la lecture globale proche de la grille du festival.
        </p>
      </div>
      <a class="planning__export" :href="exportUrl" target="_blank" rel="noopener">Exporter iCal</a>
    </header>

    <section class="planning__meta-panel">
      <div class="planning__summary">
        <article class="planning__summary-card">
          <strong>{{ summary.films }}</strong>
          <span>film(s) retenu(s)</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.selected }}</strong>
          <span>seance(s) choisie(s)</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.conflicts }}</strong>
          <span>conflit(s)</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.alternatives }}</strong>
          <span>alternative(s)</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.gaps }}</strong>
          <span>creneau(x) dispo</span>
        </article>
      </div>

      <section class="planning__controls-panel">
        <div class="planning__control-group">
          <p class="eyebrow">Vue</p>
          <div class="planning__mode-switch" role="tablist" aria-label="Mode planning">
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'plan' }" type="button" @click="planningMode = 'plan'">
              Plan choisi
            </button>
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'grid' }" type="button" @click="planningMode = 'grid'">
              Grille complete
            </button>
          </div>
        </div>

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
              {{ formatDayLabel(day) }} · {{ selectedCountForDay(day) }}
            </button>
          </div>
        </div>
      </section>
    </section>

    <section class="planning__festival-panel">
      <header class="planning__panel-header">
        <div>
          <p class="eyebrow">Vue festival</p>
          <h3>Films deja choisis dans l'ensemble du festival</h3>
        </div>
        <span>{{ selectedFestivalScreenings.length }} seance(s)</span>
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
                <strong>{{ screening.film_title }}</strong>
                <p>{{ formatTimeRange(screening) }} · {{ screening.venue_name }}</p>
              </div>
              <span class="planning__festival-state">{{ screening.selection_status === 'confirmed' ? 'Confirmee' : 'Tentative' }}</span>
            </article>
          </div>
        </article>
      </div>

      <p v-else class="planning__empty">Aucune seance choisie pour l'ensemble du festival.</p>
    </section>

    <section v-if="planningMode === 'plan'" class="planning__layout">
      <div class="planning__main">
        <article class="planning__panel">
          <header class="planning__panel-header">
            <div>
              <p class="eyebrow">Programme retenu</p>
              <h3>Plan du jour</h3>
            </div>
            <span>{{ selectedAgenda.length }} retenue(s)</span>
          </header>

          <div v-if="selectedAgenda.length" class="planning__agenda">
            <template v-for="screening in selectedAgenda" :key="screening.id">
              <article class="planning__item planning__item--selected" :class="{ 'planning__item--conflict': screening.isConflict }">
                <div class="planning__item-time">{{ formatTimeRange(screening) }}</div>
                <div class="planning__item-body">
                  <strong>{{ screening.film_title }}</strong>
                  <p>{{ screening.venue_name }}</p>
                  <p>{{ filmMeta(screening) }}</p>
                </div>
                <div class="planning__item-actions">
                  <span class="planning__state">{{ screeningReason(screening) }}</span>
                  <div class="planning__action-group">
                    <button type="button" class="planning__action" @click="setSelection(screening.id, 'tentative')">Tentative</button>
                    <button type="button" class="planning__action" @click="setSelection(screening.id, 'confirmed')">Confirmer</button>
                    <button type="button" class="planning__action planning__action--ghost" @click="setSelection(screening.id, 'none')">Retirer</button>
                  </div>
                </div>
              </article>

              <article
                v-for="gap in dayGaps.filter((entry) => entry.start === (screening.ends_at?.slice(11, 16) ?? ''))"
                :key="`${gap.dayKey}-${gap.start}-${gap.end}`"
                class="planning__gap"
              >
                <strong>Creneau disponible</strong>
                <span>{{ gap.start }} -> {{ gap.end }} · {{ formatMinutes(gap.durationMinutes) }} · {{ gapLabel(gap.durationMinutes) }}</span>
              </article>
            </template>
          </div>

          <p v-else class="planning__empty">Aucune seance choisie sur cette journee. Si tu as deja des choix ailleurs dans le festival, ils sont resumes juste au-dessus.</p>
        </article>

        <article class="planning__panel">
          <header class="planning__panel-header">
            <div>
              <p class="eyebrow">A arbitrer</p>
              <h3>Seances a placer</h3>
            </div>
            <span>{{ candidateList.length }}</span>
          </header>

          <div v-if="candidateList.length" class="planning__stack">
            <article v-for="screening in candidateList" :key="screening.id" class="planning__mini">
              <strong>{{ screening.film_title }}</strong>
              <p>{{ formatTimeRange(screening) }} · {{ screening.venue_name }}</p>
              <p>{{ filmMeta(screening) }} · {{ screeningReason(screening) }}</p>
              <div class="planning__action-group">
                <button type="button" class="planning__action" @click="setSelection(screening.id, 'tentative')">Tentative</button>
                <button type="button" class="planning__action" @click="setSelection(screening.id, 'confirmed')">Confirmer</button>
              </div>
            </article>
          </div>

          <p v-else class="planning__empty">Toutes les seances retenues de ce jour sont deja placees ou filtrees.</p>
        </article>
      </div>

      <aside class="planning__side">
        <article class="planning__panel">
          <header class="planning__panel-header">
            <div>
              <p class="eyebrow">Attention</p>
              <h3>Conflits</h3>
            </div>
            <span>{{ conflictList.length }}</span>
          </header>
          <div v-if="conflictList.length" class="planning__stack">
            <article v-for="screening in conflictList" :key="screening.id" class="planning__mini planning__mini--conflict">
              <strong>{{ screening.film_title }}</strong>
              <p>{{ formatTimeRange(screening) }} · {{ screening.venue_name }}</p>
              <p>{{ screeningReason(screening) }}</p>
              <div class="planning__action-group">
                <button type="button" class="planning__action planning__action--ghost" @click="setSelection(screening.id, 'none')">Retirer</button>
              </div>
            </article>
          </div>
          <p v-else class="planning__empty">Pas de conflit ce jour-la.</p>
        </article>

        <article class="planning__panel">
          <header class="planning__panel-header">
            <div>
              <p class="eyebrow">Second choix</p>
              <h3>Alternatives visibles</h3>
            </div>
            <span>{{ alternativesList.length }}</span>
          </header>
          <div v-if="alternativesList.length" class="planning__stack">
            <article v-for="screening in alternativesList" :key="screening.id" class="planning__mini planning__mini--alternative">
              <strong>{{ screening.film_title }}</strong>
              <p>{{ formatTimeRange(screening) }} · {{ screening.venue_name }}</p>
              <p>{{ screeningReason(screening) }}</p>
              <div class="planning__action-group">
                <button type="button" class="planning__action" @click="setSelection(screening.id, 'tentative')">Tentative</button>
                <button type="button" class="planning__action" @click="setSelection(screening.id, 'confirmed')">Confirmer</button>
              </div>
            </article>
          </div>
          <p v-else class="planning__empty">Aucune alternative ce jour-la.</p>
        </article>
      </aside>
    </section>

    <section v-else class="planning__grid-view">
      <article class="planning__panel">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Repere global</p>
            <h3>Vue d'ensemble type grille</h3>
          </div>
          <span>{{ activeDay ? formatDayLabel(activeDay) : 'Sans jour' }}</span>
        </header>

        <div class="planning__matrix">
          <div class="planning__matrix-head">Salle</div>
          <div class="planning__matrix-head">Programme</div>

          <template v-for="row in gridByVenue" :key="row.venueName">
            <div class="planning__matrix-venue">{{ row.venueName }}</div>
            <div class="planning__matrix-cell">
              <article
                v-for="screening in row.screenings"
                :key="screening.id"
                class="planning__matrix-item"
                :data-state="screening.derived_state"
              >
                <div class="planning__matrix-time">{{ formatTimeRange(screening) }}</div>
                <strong>{{ screening.film_title }}</strong>
                <p>{{ screening.film?.tagline || 'Genre non renseigne' }}</p>
              </article>
            </div>
          </template>
        </div>
      </article>
    </section>
  </section>
</template>
