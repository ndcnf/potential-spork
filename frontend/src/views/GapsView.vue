<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import PriorityBadge from '@/components/ui/PriorityBadge.vue'
import { formatMinutes, formatTimeRange, getFestivalDisplayInfo, RESERVATION_BUFFER_MINUTES } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'

const store = useFestivalStore()
const settingsStore = useSettingsStore()
const ignoredGapKeys = ref(new Set<string>())

function isPlannablePriority(priority: string): boolean {
  return priority === 'medium' || priority === 'high' || priority === 'must-see'
}

const gapMessages = [
  { min: 15, max: 15, label: 'Faudra courir' },
  { min: 16, max: 45, label: 'Tu peux souffler un peu' },
  { min: 46, max: 120, label: "T'as pense a manger ?" },
  { min: 121, max: Number.POSITIVE_INFINITY, label: "C'est un jour de conge ?" },
]

onMounted(() => {
  settingsStore.load()
  if (!store.cycles.length && !store.loading) {
    store.bootstrap()
  }
})

const plannableFilmIds = computed(
  () => new Set(store.films.filter((film) => isPlannablePriority(film.priority)).map((film) => film.id)),
)

const filmById = computed(() => new Map(store.films.map((film) => [film.id, film])))

const selectedScreenings = computed(() =>
  store.visibleScreenings
    .filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
    .filter((screening) => screening.starts_at && screening.ends_at)
    .sort((left, right) => {
      const leftInfo = getFestivalDisplayInfo(left.starts_at)
      const rightInfo = getFestivalDisplayInfo(right.starts_at)
      return leftInfo.displayDayKey.localeCompare(rightInfo.displayDayKey) || leftInfo.displayMinutes - rightInfo.displayMinutes
    }),
)

const allPlannableScreenings = computed(() =>
  store.visibleScreenings
    .filter((screening) => plannableFilmIds.value.has(screening.film_id))
    .filter((screening) => screening.starts_at && screening.ends_at)
    .sort((left, right) => {
      const leftInfo = getFestivalDisplayInfo(left.starts_at)
      const rightInfo = getFestivalDisplayInfo(right.starts_at)
      return leftInfo.displayDayKey.localeCompare(rightInfo.displayDayKey) || leftInfo.displayMinutes - rightInfo.displayMinutes
    }),
)

const gapSections = computed(() => {
  const selectedByDay = new Map<string, typeof selectedScreenings.value>()
  for (const screening of selectedScreenings.value) {
    const day = getFestivalDisplayInfo(screening.starts_at).displayDayKey
    selectedByDay.set(day, [...(selectedByDay.get(day) ?? []), screening])
  }

  const allByDay = new Map<string, typeof allPlannableScreenings.value>()
  for (const screening of allPlannableScreenings.value) {
    const day = getFestivalDisplayInfo(screening.starts_at).displayDayKey
    allByDay.set(day, [...(allByDay.get(day) ?? []), screening])
  }

  return [...allByDay.entries()].flatMap(([day, screenings]) => {
    const selected = [...(selectedByDay.get(day) ?? [])].sort((left, right) => getFestivalDisplayInfo(left.starts_at).displayMinutes - getFestivalDisplayInfo(right.starts_at).displayMinutes)
    const sortedDay = [...screenings].sort((left, right) => getFestivalDisplayInfo(left.starts_at).displayMinutes - getFestivalDisplayInfo(right.starts_at).displayMinutes)
    const dayStart = sortedDay[0]
    const dayEnd = sortedDay[sortedDay.length - 1]

    if (!dayStart || !dayEnd) {
      return []
    }

    const windows: Array<{ startMinutes: number; endMinutes: number; startLabel: string; endLabel: string; key: string }> = []

    if (selected.length === 0) {
      windows.push({
        startMinutes: getFestivalDisplayInfo(dayStart.starts_at).displayMinutes,
        endMinutes: getFestivalDisplayInfo(dayEnd.ends_at).displayMinutes,
        startLabel: dayStart.starts_at?.slice(11, 16) ?? '--:--',
        endLabel: dayEnd.ends_at?.slice(11, 16) ?? '--:--',
        key: `${day}-full-day`,
      })
    } else {
      const firstSelected = selected[0]
      const beforeDuration = getFestivalDisplayInfo(firstSelected.starts_at).displayMinutes - getFestivalDisplayInfo(dayStart.starts_at).displayMinutes
      if (beforeDuration >= RESERVATION_BUFFER_MINUTES) {
        windows.push({
          startMinutes: getFestivalDisplayInfo(dayStart.starts_at).displayMinutes,
          endMinutes: getFestivalDisplayInfo(firstSelected.starts_at).displayMinutes,
          startLabel: dayStart.starts_at?.slice(11, 16) ?? '--:--',
          endLabel: firstSelected.starts_at?.slice(11, 16) ?? '--:--',
          key: `${day}-before-first`,
        })
      }

      for (let index = 0; index < selected.length - 1; index += 1) {
        const previous = selected[index]
        const next = selected[index + 1]
        const previousEnd = getFestivalDisplayInfo(previous.ends_at).displayMinutes
        const nextStart = getFestivalDisplayInfo(next.starts_at).displayMinutes
        const gapDuration = nextStart - previousEnd

        if (gapDuration >= RESERVATION_BUFFER_MINUTES) {
          windows.push({
            startMinutes: previousEnd,
            endMinutes: nextStart,
            startLabel: previous.ends_at?.slice(11, 16) ?? '--:--',
            endLabel: next.starts_at?.slice(11, 16) ?? '--:--',
            key: `${day}-between-${index}`,
          })
        }
      }

      const lastSelected = selected[selected.length - 1]
      const afterDuration = getFestivalDisplayInfo(dayEnd.ends_at).displayMinutes - getFestivalDisplayInfo(lastSelected.ends_at).displayMinutes
      if (afterDuration >= RESERVATION_BUFFER_MINUTES) {
        windows.push({
          startMinutes: getFestivalDisplayInfo(lastSelected.ends_at).displayMinutes,
          endMinutes: getFestivalDisplayInfo(dayEnd.ends_at).displayMinutes,
          startLabel: lastSelected.ends_at?.slice(11, 16) ?? '--:--',
          endLabel: dayEnd.ends_at?.slice(11, 16) ?? '--:--',
          key: `${day}-after-last`,
        })
      }
    }

    return windows.flatMap((window) => {
      const gapDuration = window.endMinutes - window.startMinutes
      const minimumGapMinutes = Math.max(RESERVATION_BUFFER_MINUTES, settingsStore.recommendationSettings.minGapMinutes)
      if (gapDuration < minimumGapMinutes) {
        return []
      }

      const candidates = store.visibleScreenings
        .filter((screening) => screening.selection_status === 'none')
        .filter((screening) => plannableFilmIds.value.has(screening.film_id))
        .filter((screening) => getFestivalDisplayInfo(screening.starts_at).displayDayKey === day)
        .filter((screening) => screening.starts_at && screening.ends_at)
        .filter((screening) => {
          const screeningStart = getFestivalDisplayInfo(screening.starts_at).displayMinutes
          const screeningEnd = getFestivalDisplayInfo(screening.ends_at).displayMinutes
          const startsTooEarly =
            settingsStore.recommendationSettings.avoidBeforeMinutes !== null &&
            screeningStart < settingsStore.recommendationSettings.avoidBeforeMinutes
          const endsTooLate =
            settingsStore.recommendationSettings.avoidAfterMinutes !== null &&
            screeningEnd > settingsStore.recommendationSettings.avoidAfterMinutes
          return (
            !startsTooEarly &&
            !endsTooLate &&
            screeningStart >= window.startMinutes + RESERVATION_BUFFER_MINUTES &&
            screeningEnd <= window.endMinutes - RESERVATION_BUFFER_MINUTES
          )
        })
        .map((screening) => ({
          id: screening.id,
          title: screening.film_title,
          venue: screening.venue_name,
          timeRange: formatTimeRange(screening.starts_at, screening.ends_at),
          priority: filmById.value.get(screening.film_id)?.priority ?? 'medium',
        }))
        .sort((left, right) => left.timeRange.localeCompare(right.timeRange) || left.title.localeCompare(right.title))

      const message = gapMessages.find((entry) => gapDuration >= entry.min && gapDuration <= entry.max)?.label ?? 'Creneau libre'

      return [{
        key: window.key,
        day,
        start: window.startLabel,
        end: window.endLabel,
        durationMinutes: gapDuration,
        message,
        candidates,
      }]
    })
  })
})

const groupedGapSections = computed(() => {
  const grouped = new Map<string, typeof gapSections.value>()

  for (const gap of gapSections.value) {
    if (ignoredGapKeys.value.has(gap.key)) {
      continue
    }

    grouped.set(gap.day, [...(grouped.get(gap.day) ?? []), gap])
  }

  return [...grouped.entries()].map(([day, gaps]) => ({
    day,
    gaps,
  }))
})

function formatDay(day: string): string {
  const date = new Date(`${day}T12:00:00`)
  return new Intl.DateTimeFormat('fr-CH', { weekday: 'long', day: '2-digit', month: '2-digit' }).format(date)
}

function addTentative(screeningId: number): void {
  store.setScreeningSelection(screeningId, 'tentative')
}

function ignoreGap(gapKey: string): void {
  ignoredGapKeys.value = new Set([...ignoredGapKeys.value, gapKey])
}
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Etape 3</p>
        <h2>Creneaux libres</h2>
        <p class="page-copy">
          Seances qui peuvent s'ajouter sans conflit, avec 15 minutes de buffer minimum entre deux projections.
        </p>
      </div>
    </header>

    <section class="gap-suggestions gap-suggestions--single">
      <article v-for="dayGroup in groupedGapSections" :key="dayGroup.day" class="gap-day-group">
        <header class="gap-day-group__header">
          <p class="eyebrow">Jour</p>
          <h3>{{ formatDay(dayGroup.day) }}</h3>
          <span>{{ dayGroup.gaps.length }} creneau(x)</span>
        </header>

        <div class="gap-day-group__list">
          <article v-for="gap in dayGroup.gaps" :key="gap.key" class="gap-card">
            <div class="gap-card-main">
              <div>
                <p class="eyebrow">Creneau</p>
                <h3>{{ gap.start }} -> {{ gap.end }}</h3>
              </div>
              <div class="planning__item-actions">
                <strong>{{ formatMinutes(gap.durationMinutes) }}</strong>
                <button type="button" class="planning__action planning__action--ghost" @click="ignoreGap(gap.key)">Ignorer</button>
              </div>
            </div>

            <p>{{ gap.message }}</p>

            <div v-if="gap.candidates.length" class="planning__stack">
              <article v-for="candidate in gap.candidates" :key="candidate.id" class="planning__mini planning__mini--alternative">
                <div>
                  <strong>{{ candidate.title }}</strong>
                  <p>{{ candidate.timeRange }} · {{ candidate.venue }}</p>
                </div>
                <div class="planning__item-actions">
                  <PriorityBadge :priority="candidate.priority" />
                  <button type="button" class="planning__action" @click="addTentative(candidate.id)">Ajouter au planning</button>
                </div>
              </article>
            </div>

            <p v-else class="planning__empty">Aucune seance compatible dans ce creneau pour l'instant.</p>
          </article>
        </div>
      </article>

      <p v-if="!groupedGapSections.length" class="planning__empty">Aucun creneau visible pour l'instant.</p>
    </section>
  </section>
</template>
