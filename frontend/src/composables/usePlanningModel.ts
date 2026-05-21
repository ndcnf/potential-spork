import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { formatMinutes, formatTimeRange as formatTimeRangeValue, getFestivalDisplayInfo, screeningsOverlapWithBuffer, toMinutes } from '@/lib/planning'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
import type { Film, Screening } from '@/types'

export type PlanningScreening = Screening & {
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
  visualRowStart?: number
  visualRowSpan?: number
}

export const FESTIVAL_VIEW_KEY = '__festival__'

export function usePlanningModel() {
  const store = useFestivalStore()
  const settingsStore = useSettingsStore()
  const activeDay = ref('')
  const planningMode = ref<'timeline' | 'venues' | 'visualization'>('timeline')
  const detailScreeningId = ref<number | null>(null)
  const isMobile = ref(false)
  let mobileMedia: MediaQueryList | null = null

  const syncMobileMode = () => {
    isMobile.value = mobileMedia?.matches ?? false
  }

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

  function countConflictPairs(screenings: Screening[]): number {
    let count = 0

    for (let index = 0; index < screenings.length; index += 1) {
      for (let otherIndex = index + 1; otherIndex < screenings.length; otherIndex += 1) {
        if (screeningsOverlapWithBuffer(screenings[index], screenings[otherIndex])) {
          count += 1
        }
      }
    }

    return count
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      const breakpoint = getComputedStyle(document.documentElement).getPropertyValue('--breakpoint-mobile').trim() || '960px'
      mobileMedia = window.matchMedia(`(max-width: ${breakpoint})`)
      syncMobileMode()
      mobileMedia.addEventListener('change', syncMobileMode)
    }

    settingsStore.load()
    if (!store.cycles.length && !store.loading) {
      store.bootstrap()
    }
  })

  onBeforeUnmount(() => {
    mobileMedia?.removeEventListener('change', syncMobileMode)
  })

  const effectivePlanningMode = computed(() => (isMobile.value && planningMode.value === 'visualization' ? 'timeline' : planningMode.value))

  const filmById = computed(() => new Map(store.films.map((film) => [film.id, film])))

  const plannableFilmIds = computed(() => new Set(store.films.filter((film) => isPlanningPriority(film.priority)).map((film) => film.id)))

  const planningScreenings = computed<PlanningScreening[]>(() => {
    const baseScreenings = store.visibleScreenings.filter((screening) => screening.starts_at && screening.ends_at && plannableFilmIds.value.has(screening.film_id))
    const selectedScreenings = baseScreenings.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
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
      if (screening.selection_status === 'rejected') continue
      candidatesByFilmId.set(screening.film_id, [...(candidatesByFilmId.get(screening.film_id) ?? []), screening])
    }

    for (const [filmId, screenings] of candidatesByFilmId.entries()) {
      const hasSelected = screenings.some((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
      if (hasSelected) continue

      if (settingsStore.recommendationMode === 'personalized') {
        const scored = [...screenings]
          .map((screening) => ({ screening, ...screeningRecommendationScore(screening, selectedScreenings, screenings.length) }))
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
        const startInfo = getFestivalDisplayInfo(screening.starts_at)
        const endInfo = getFestivalDisplayInfo(screening.ends_at)
        const isSelected = screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'
        const film = filmById.value.get(screening.film_id) ?? null
        const isSingleScreening = (validScreeningCountByFilmId.get(screening.film_id) ?? 0) === 1
        const isMustLock = isSingleScreening && isHighPriority(film?.priority) && !isSelected
        const isRecommended = recommendationByFilmId.get(screening.film_id) === screening.id && !isSelected

        return {
          ...screening,
          film,
          dayKey: startInfo.displayDayKey,
          startMinutes: startInfo.displayMinutes,
          endMinutes: endInfo.displayMinutes,
          isSelected,
          isConflict: selectedScreenings.some((other) => screeningsOverlapWithBuffer(screening, other)),
          isAlternative: selectedFilmIds.has(screening.film_id) && screening.selection_status === 'none',
          isSingleScreening,
          isMustLock,
          isRecommended,
          recommendationNote: recommendationNoteByScreeningId.get(screening.id) ?? null,
          recommendationReasons: recommendationReasonsByScreeningId.get(screening.id) ?? [],
        }
      })
      .sort((left, right) => left.dayKey.localeCompare(right.dayKey) || left.startMinutes - right.startMinutes || left.film_title.localeCompare(right.film_title))
  })

  const dayKeys = computed(() => [...new Set(planningScreenings.value.map((screening) => screening.dayKey))])
  const dayOptions = computed(() => [FESTIVAL_VIEW_KEY, ...dayKeys.value])

  watch(dayKeys, (days) => {
    if (!days.length) {
      activeDay.value = ''
      return
    }
    if (!activeDay.value || (activeDay.value !== FESTIVAL_VIEW_KEY && !days.includes(activeDay.value))) {
      activeDay.value = FESTIVAL_VIEW_KEY
    }
  }, { immediate: true })

  const dayScreenings = computed(() => activeDay.value === FESTIVAL_VIEW_KEY ? planningScreenings.value : planningScreenings.value.filter((screening) => screening.dayKey === activeDay.value))

  const timelineGroups = computed(() => {
    if (activeDay.value !== FESTIVAL_VIEW_KEY) {
      return [{ dayKey: activeDay.value, screenings: dayScreenings.value }]
    }

    const grouped = new Map<string, PlanningScreening[]>()
    for (const screening of dayScreenings.value) {
      grouped.set(screening.dayKey, [...(grouped.get(screening.dayKey) ?? []), screening])
    }

    return [...grouped.entries()].map(([dayKey, screenings]) => ({ dayKey, screenings }))
  })

  const detailScreening = computed(() => planningScreenings.value.find((screening) => screening.id === detailScreeningId.value) ?? null)

  const relatedFilmScreenings = computed(() => {
    if (!detailScreening.value) {
      return [] as PlanningScreening[]
    }

    return planningScreenings.value
      .filter((screening) => screening.film_id === detailScreening.value?.film_id)
      .sort((left, right) => left.startMinutes - right.startMinutes)
  })

  const selectedConflictCount = computed(() => {
    const selected = planningScreenings.value.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')
    return countConflictPairs(selected)
  })

  const summary = computed(() => ({
    films: store.films.filter((film) => isPlanningPriority(film.priority)).length,
    selected: planningScreenings.value.filter((screening) => screening.isSelected).length,
    conflicts: selectedConflictCount.value,
    toPlace: planningScreenings.value.filter((screening) => !screening.isSelected && !screening.isAlternative && screening.selection_status !== 'rejected').length,
  }))

  const daySummary = computed(() => ({
    total: dayScreenings.value.length,
    selected: dayScreenings.value.filter((screening) => screening.isSelected).length,
    conflicts: countConflictPairs(dayScreenings.value.filter((screening) => screening.selection_status === 'tentative' || screening.selection_status === 'confirmed')),
  }))

  const gridVenueNames = computed(() => [...new Set(dayScreenings.value.map((screening) => screening.venue_name || 'Salle inconnue'))].sort((left, right) => left.localeCompare(right)))

  const gridByVenue = computed(() => gridVenueNames.value.map((venueName) => ({
    venueName,
    screenings: dayScreenings.value.filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName),
  })))

  const venueGroups = computed(() => {
    if (activeDay.value !== FESTIVAL_VIEW_KEY) {
      return [{ dayKey: activeDay.value, venues: gridByVenue.value }]
    }

    return timelineGroups.value.map((group) => {
      const venueNames = [...new Set(group.screenings.map((screening) => screening.venue_name || 'Salle inconnue'))].sort((left, right) => left.localeCompare(right))
      return {
        dayKey: group.dayKey,
        venues: venueNames.map((venueName) => ({
          venueName,
          screenings: group.screenings.filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName),
        })),
      }
    })
  })

  const visualizationGroups = computed(() => {
    const sourceGroups = activeDay.value === FESTIVAL_VIEW_KEY ? timelineGroups.value : [{ dayKey: activeDay.value, screenings: dayScreenings.value }]

    return sourceGroups.map((group) => {
      const allScreenings = group.screenings
      if (!allScreenings.length) {
        return { dayKey: group.dayKey, bucketLabels: [] as string[], lanes: [] as Array<{ venueName: string; blocks: PlanningScreening[] }> }
      }

      const minMinutes = Math.min(...allScreenings.map((screening) => screening.startMinutes))
      const maxMinutes = Math.max(...allScreenings.map((screening) => screening.endMinutes))
      const dayStart = Math.floor(minMinutes / 15) * 15
      const dayEnd = Math.ceil(maxMinutes / 15) * 15
      const bucketCount = Math.max(1, (dayEnd - dayStart) / 15)

      const bucketLabels = Array.from({ length: bucketCount + 1 }, (_, index) => {
        const totalMinutes = dayStart + index * 15
        const hours = Math.floor(totalMinutes / 60) % 24
        const minutes = totalMinutes % 60
        return `${String(hours).padStart(2, '0')}h${String(minutes).padStart(2, '0')}`
      })

      const venueNames = [...new Set(allScreenings.map((screening) => screening.venue_name || 'Salle inconnue'))].sort((left, right) => left.localeCompare(right))

      return {
        dayKey: group.dayKey,
        bucketLabels,
        bucketCount,
        dayStart,
        lanes: venueNames.map((venueName) => ({
          venueName,
          blocks: allScreenings
            .filter((screening) => (screening.venue_name || 'Salle inconnue') === venueName)
            .map((screening) => ({
              ...screening,
              visualRowStart: Math.floor((screening.startMinutes - dayStart) / 15) + 1,
              visualRowSpan: Math.max(1, Math.ceil((screening.endMinutes - screening.startMinutes) / 15)),
            })),
        })),
      }
    })
  })

  watch([activeDay, detailScreening], ([day, screening]) => {
    if (!screening) return
    if (day !== FESTIVAL_VIEW_KEY && screening.dayKey !== day) {
      detailScreeningId.value = null
    }
  })

  function formatDayLabel(dayKey: string): string {
    const date = new Date(`${dayKey}T12:00:00`)
    return new Intl.DateTimeFormat('fr-CH', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(date)
  }

  function formatDayChipLabel(dayKey: string): string {
    const date = new Date(`${dayKey}T12:00:00`)
    const weekday = new Intl.DateTimeFormat('fr-CH', { weekday: 'short' }).format(date).replace('.', '').toLowerCase()
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
      const conflictingSelected = planningScreenings.value.find((other) => other.id !== screening.id && (other.selection_status === 'tentative' || other.selection_status === 'confirmed') && screeningsOverlapWithBuffer(screening, other))
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

  function visualizationBlockClass(screening: PlanningScreening): string {
    if (screening.isSelected && screening.isConflict) {
      return screening.selection_status === 'confirmed' ? 'planning__visual-block--confirmed-conflict' : 'planning__visual-block--tentative-conflict'
    }
    if (screening.selection_status === 'confirmed') return 'planning__visual-block--confirmed'
    if (screening.selection_status === 'tentative') return 'planning__visual-block--tentative'
    if (screening.selection_status === 'rejected') return 'planning__visual-block--rejected'
    if (screening.isAlternative || screening.derived_state === 'disabled') return 'planning__visual-block--disabled'
    if (screening.isMustLock) return 'planning__visual-block--must-lock'
    if (screening.isRecommended) return 'planning__visual-block--recommended'
    if (screening.derived_state === 'conflict' || screening.isConflict) return 'planning__visual-block--conflict'
    return 'planning__visual-block--available'
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

  function toggleScreeningSelection(screeningId: number, nextStatus: Screening['selection_status']): void {
    const screening = planningScreenings.value.find((item) => item.id === screeningId)
    if (!screening) return
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

  return {
    store,
    settingsStore,
    activeDay,
    planningMode,
    detailScreeningId,
    isMobile,
    effectivePlanningMode,
    planningScreenings,
    dayKeys,
    dayOptions,
    dayScreenings,
    timelineGroups,
    detailScreening,
    relatedFilmScreenings,
    summary,
    daySummary,
    venueGroups,
    visualizationGroups,
    formatDayLabel,
    formatTimeRange,
    filmMeta,
    screeningReason,
    screeningStateClass,
    visualizationBlockClass,
    selectedCountForDay,
    dayChipLabel,
    toggleScreeningSelection,
    jumpToDay,
    openDetailPanel,
    closeDetailPanel,
    exportUrl,
    FESTIVAL_VIEW_KEY,
  }
}
